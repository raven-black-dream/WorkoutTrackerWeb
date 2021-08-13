import csv
import os
import pandas
import pickle
import numpy
from .models import Set, ExpectedSet, ProgramDay, ExerciseType, Workout
from sklearn import svm


class Predictor:

    def __init__(self, day, user):
        self.previous_data = self.get_previous_data(day, user)
        self.day = self.get_program_day(day)
        self.user = user
        if not os.path.exists("RFCModel.pkl"):
            self.train_svc()
        self.model = pickle.load(open("RFCModel.pkl", 'rb'))

    def fit_svc(self):
        if self.previous_data.empty:
            return None
        ex_data = self.create_exercise_dataset()
        ex_data['user_id'] = self.user
        ex_data['suggestion'] = self.model.predict(ex_data[['min_reps', 'max_reps', 'reps', 'rpe', 'set_num', 'user_id']])
        return ex_data

    def create_exercise_dataset(self):
        prev_data = self.previous_data.copy()
        prev_data["weight"] = pandas.to_numeric(prev_data["weight"])
        data = pandas.DataFrame()
        exercise_list = self.previous_data.exercise_id.unique()
        rep_ranges = self.get_rep_ranges()
        for exercise in exercise_list:
            exercise_data = self.get_exercise_data(exercise)
            most_recent = exercise_data['workout_id'][0]
            ex_data = prev_data[(prev_data["workout_id"] == most_recent) & (prev_data["exercise_id"] == exercise)].copy()
            ex_data['rpe'] = ex_data['rpe'].astype('int64')
            ex_data = ex_data.groupby('exercise_id').agg({
                "reps": "mean",
                "weight": "mean",
                'rpe': 'mean'})
            ex_data = ex_data.reset_index()
            rep_data = self.day.loc[self.day['exercise_id'] == exercise].copy()
            rep_data = rep_data.groupby('exercise_id').agg({'reps_min': 'mean',
                                                            'reps_max': 'mean',
                                                            'set_num': 'max'})
            rep_data = rep_data.reset_index()
            ex_data['min_reps'] = rep_data['reps_min']
            ex_data['max_reps'] = rep_data['reps_max']
            ex_data['set_num'] = rep_data['set_num']
            data = data.append(ex_data)

        return data

    def get_rep_ranges(self):
        rep_ranges = {}
        exercise_list = self.day.exercise_id.unique()
        for exercise in exercise_list:
            ex_data = self.day[self.day['exercise_id'] == exercise]
            ex_reps = [(mn, mx, amrap) for mn, mx, amrap in zip(ex_data['reps_min'], ex_data['reps_max'], ex_data['amrap'])]
            rep_ranges[exercise] = list(set(ex_reps))
            if len(rep_ranges[exercise]) == 2:
                rng1 = rep_ranges[exercise][0]
                rng2 = rep_ranges[exercise][1]
                rep_ranges[exercise] = [(int((rng1[0] + rng2[0])/2), int((rng1[1] + rng2[1])/2))]
        return rep_ranges

    def get_exercise_data(self, exercise):
        temp = self.previous_data.copy()
        workout_ids = self.get_workouts()
        valid_workouts = temp[temp.workout_id.isin(workout_ids)]
        if not workout_ids or exercise not in valid_workouts.exercise_id.tolist():
            original_data = temp[temp['exercise_id'] == exercise]
        else:
            original_data = valid_workouts[valid_workouts['exercise_id'] == exercise]
        exercise_data = original_data.groupby('workout_id').agg(
            {
                'exercise_id': 'max',
                'reps': 'mean'
            }
        ).copy()
        exercise_data = exercise_data.reset_index()
        exercise_data['rounded'] = round(exercise_data['reps'])
        max_reps = max(exercise_data['rounded'])
        data = []
        for rep in range(1, int(max_reps)+1):
            if rep in exercise_data['rounded'].values:
                rep_data = exercise_data.copy()
                rep_data = rep_data[rep_data['rounded'] == rep]
                recent_workout = max(rep_data['workout_id'])
                data.append({'reps': rep, 'workout_id': recent_workout})
            elif rep in original_data['reps'].values:
                rep_data = original_data.copy()
                rep_data = rep_data[rep_data['reps'] == rep]
                recent_workout = max(rep_data['workout_id'])
                data.append({'reps': rep, 'workout_id': recent_workout})

        data = pandas.DataFrame(data)
        return data

    def parse_data(self, recommended=None):
        data = []
        i = 1
        exercise_names = {ex.exercise_id: ex for ex in ExerciseType.objects.all()}
        for exercise in self.day.exercise_id.unique():
            ex_data = self.day[self.day['exercise_id'] == exercise].copy()
            sets = ex_data.set_num.unique()
            exercise_obj = exercise_names[exercise]
            exercise_name = exercise_names[exercise].name
            for set_num in sets:
                ex_set = ex_data[ex_data['set_num'] == set_num].copy()
                j = ex_set.index[ex_set['set_num'] == set_num].tolist()[0]
                set_data = {'exercise': exercise_obj}
                if not recommended or exercise_name not in recommended.keys():
                    set_data['weight'] = 0
                else:
                    if not ex_set['amrap'][j]:
                        set_data['weight'] = int(recommended[exercise_name])
                    elif ex_set['amrap'][j]:
                        set_data['weight'] = int(recommended[exercise_name])
                    else:
                        set_data['weight'] = 0
                set_data['order'] = i
                set_data['set_number'] = ex_set['set_num'][j]
                if ex_set['reps_min'][j] == ex_set['reps_max'][j]:
                    set_data['reps'] = ex_set['reps_min'][j]
                elif ex_set['amrap'][j] == 1:
                    set_data['reps'] = 0
                else:
                    set_data['reps'] = ex_set['reps_min'][j]
                set_data['RPE'] = pandas.to_numeric(ex_set['rpe'][j])
                data.append(set_data)
            i += 1
        return data

    def predict(self):
        data = {}
        fitted = self.fit_svc()
        if fitted is None:
            return self.parse_data()
        exercise_names = {ex.exercise_id: ex.name for ex in ExerciseType.objects.all()}
        exercise_modifiers = {ex.name: ex.weight_step for ex in ExerciseType.objects.all()}
        exercise_types = {ex.name: ex.weighted for ex in ExerciseType.objects.all()}
        for exercise in fitted.exercise_id.unique():
            exercise_data = fitted[fitted["exercise_id"] == exercise]
            exercise_name = exercise_names[exercise]
            data[exercise_name] = {}
            if exercise_types[exercise_name]:

                degree = numpy.floor((exercise_data['reps']-exercise_data['max_reps'])+1) * exercise_data["suggestion"][0]
                value = (degree * float(exercise_modifiers[exercise_name]))
                base = float(exercise_modifiers[exercise_name])
                data[exercise_name] = exercise_data['weight'].iat[0] + self.rounding_for_weights(value.iat[0], base)
            else:
                data[exercise_name] = 0

        return self.parse_data(data)

    def interpolate_missing_vals(self, data, rnge):
        min_val = min(data['min_reps'])
        min_data = data[data['min_reps'] == min_val].copy()
        weight = min_data["weight"][0]
        reps = min_data['reps'][0]
        one_rm = self.calculate_one_rep_max(weight, reps)
        percent = self.calculate_percentage_from_reps((rnge[0] + rnge[1])/2)
        value = numpy.floor((one_rm * percent)*0.95)
        return value

    def get_workouts(self):
        day_id = self.day.day_id.max()
        workouts = Workout.objects.filter(expected=day_id).filter(user_id=self.user).all().values('workout_id')
        if workouts:
            workouts = [workout['workout_id'] for workout in workouts]
        else:
            workouts = []
        return workouts

    @staticmethod
    def get_exercise_modifiers():
        data = {}
        with open('exercise_modifiers.csv', 'r') as infile:
            for row in csv.DictReader(infile):
                data.update({row['Exercise']: float(row['Modifier'])})
        return data

    @staticmethod
    def get_previous_data(day, user):
        exercise_list = list(set([ex.exercise.pk for ex in day]))
        previous_data = pandas.DataFrame.from_records(
            Set.objects.filter(workout__user_id=user).filter(exercise__in=exercise_list).all().values())
        return previous_data

    @staticmethod
    def get_program_day(day):
        day_data = list(day.all().values())
        data = pandas.DataFrame.from_records(day_data)
        return data

    @staticmethod
    def calculate_one_rep_max(weight, reps):
        numerator = 100 * weight
        denominator = 48.8 + (53.8*numpy.exp(-0.075 * reps))
        return numerator/denominator

    @staticmethod
    def calculate_percentage_from_reps(reps):
        percent = 0.00044*(reps**2) - 0.0303*reps + 1.03
        return percent

    @staticmethod
    def rounding_for_weights(value, base):
        return base * round(value/base)

    @staticmethod
    def train_svc():
        data = pandas.read_csv("training_data.csv")
        svc = svm.SVC(decision_function_shape='ovo', degree=1, kernel='poly', probability=True)
        x = data[["scaled_by_min", "scaled_by_max"]]
        y = data["result"]
        svc.fit(x, y)
        pickle.dump(svc, open("SVCModel.pkl", 'wb'))
