from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views import generic
from django.db.models import Avg, Max
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import datetime
from .models import Workout, WAUser, Program, UserWeight, UserProgram, Set, ProgramDay, ExpectedSet, UnitType
from .forms import UserWeightForm, UserProgramForm, DaySelectorForm, SetFormSet, ExpectedSetFormset, ProgramDayForm
from .forms import WorkoutForm, AddUserForm
from .ml import Predictor
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import Select, CustomJS, ColumnDataSource
from bokeh.layouts import column
import pandas
import numpy


def index(request):
    return render(request, 'WorkoutAppWebGUI/index.html', {})


def contact(request):
    return render(request, 'WorkoutAppWebGUI/contact.html', {})


def remove_day(request, *args, **kwargs):
    if request.POST:
        day = ProgramDay.objects.filter(pk=kwargs['day_id'])
        day.delete()

    return reverse('program_day_list', kwargs={'pk': kwargs['program_id']})


@login_required()
def landing(request):
    context = {}
    user = get_object_or_404(WAUser, pk=request.user.wauser.pk)
    context['exercise_history'] = user.workout_set.order_by('-workout_id')[:10][::-1]
    data = Set.objects.filter(workout__in=user.workout_set.all()).values('workout__date', 'exercise__name').\
        order_by("workout__date").annotate(avg_reps=Avg('reps'), avg_weight=Avg('weight'))
    context['script'], context['div'] = plot(data)
    return render(request, "WorkoutAppWebGUI/landing.html", context)


def plot(input_data):
    df = pandas.DataFrame(input_data)
    df['one-rep-max'] = df.apply(calculate_one_rep_max, axis=1)
    df = df.drop(['avg_reps', 'avg_weight'], axis=1)
    df['workout__date'] = pandas.to_datetime(df.workout__date)
    df = df.set_index(keys='workout__date')
    data = ColumnDataSource(data=df)
    menu = list(df.exercise__name.unique())
    cur_data = ColumnDataSource(data=dict(x=[], y=[], z=[]))
    callback = CustomJS(args=dict(source=data, ss=cur_data), code="""
        var f = cb_obj.value
        var d2 = ss.data
        d2['x'] = []
        d2['y'] = []
        d2['z'] = []
        
        for(var i = 0; i <= source.get_length(); i++){
            if (source.data['exercise__name'][i] == f){
                d2['x'].push(source.data['workout__date'][i])
                d2['y'].push(source.data['one-rep-max'][i])
                d2['z'].push(source.data['exercise__name'][i])
            }
        }
        ss.change.emit();
        """)
    exercise_chooser = Select(title="Exercise", options=menu)
    exercise_chooser.sizing_mode = 'scale_width'
    exercise = '' if cur_data.data['z'] == [] else cur_data.data['z'][0]
    fig = figure(title=f"Estimated One Rep Max - {exercise}", x_axis_label="Date", x_axis_type='datetime',
                 y_axis_label="Estimated One Rep Max")
    fig.sizing_mode = "scale_both"
    fig.line(x='x', y='y', source=cur_data)
    exercise_chooser.js_on_change("value", callback)
    layout = column(exercise_chooser, fig)
    layout.sizing_mode = "scale_width"
    script, div = components(layout)
    return script, div


def calculate_one_rep_max(row):
    numerator = 100 * row['avg_weight']
    denominator = 48.8 + (53.8 * numpy.exp(-0.075 * row['avg_reps']))
    return float(numerator) / float(denominator)


@login_required()
def edit_user(request):
    user = get_object_or_404(WAUser, pk=request.user.wauser.pk)
    form2 = UserWeightForm(request.POST or None, instance=user)
    form3 = UserProgramForm(request.POST or None, instance=user)
    forms = [form2, form3]
    for form in forms:
        if form.is_valid():
            form.save()
            return redirect(f'users/{request.user.wauser.pk}')
    return render(request, "WorkoutAppWebGUI/profile_edit.html", {'forms': forms})


def choose_day(request):
    user = get_object_or_404(WAUser, pk=request.user.wauser.pk)
    form = DaySelectorForm
    user_program = UserProgram.objects.filter(user_id=user.pk).filter(current=1).first()
    days = user_program.program.programday_set.all()
    choices = [((day.program.program_id, day.day_name), day.day_name) for day in days]
    choices.insert(0, ((None, "Different Workout"), "Different Workout"))
    form.declared_fields['day_selector'].choices = choices
    if request.GET:
        temp = request.GET['day_selector']
        temp = temp[1:-1].split(', ')
        program_id = int(temp[0])
        day_name = temp[1][1:-1]
        if day_name != "Different Workout":
            day = ProgramDay.objects.filter(program_id=program_id).filter(day_name=day_name).first()
            return redirect('add_workout', day_id=day.program_day_id)
        else:
            context = {}
            return render(request, '', context)
    return render(request, "WorkoutAppWebGUI/day_selector.html", {'form': form,
                                                                  'program': user_program.program.program_name})


class UserView(LoginRequiredMixin, generic.DetailView):
    model = WAUser
    template_name = 'WorkoutAppWebGUI/profile.html'
    login_url = 'login/'
    redirect_field_name = ''
    context_object_name = "UserDetails"

    def get_queryset(self):
        query_set = super(UserView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        return query_set

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        context['user_data'] = WAUser.objects.filter(user_id=self.kwargs['pk']).first()
        context['weight_data'] = UserWeight.objects.filter(user_id=self.kwargs['pk']).all()
        context['user_weight'] = UserWeight.objects.filter(user_id=self.kwargs['pk']).order_by('seq_num').last()
        program = UserProgram.objects.filter(user_id=self.kwargs['pk']).filter(current=1).first()
        context['program'] = Program.objects.get(pk=program.program_id)
        return context


class AddUser(LoginRequiredMixin, generic.edit.CreateView):
    model = User
    form_class = AddUserForm
    template_name = 'WorkoutAppWebGUI/add_user.html'

    def form_valid(self, form):
        user = form.save()
        wauser = WAUser(first_name=user.first_name, last_name=user.last_name, auth_user=user)
        wauser.save()
        return super().form_valid(form)


class ProgramView(LoginRequiredMixin, generic.DetailView):
    model = UserProgram
    template_name = 'WorkoutAppWebGUI/program.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_context_data(self, **kwargs):
        context = super(ProgramView, self).get_context_data(**kwargs)
        program = UserProgram.objects.filter(user_id=self.request.user.wauser.pk).filter(current=1).first()
        context['program'] = program.program
        program_days = program.program.programday_set.all()
        context['program_days'] = {program_day.day_name:
                                       program_day.expectedset_set.all() for program_day in program_days}
        return context


class WorkoutView(LoginRequiredMixin, generic.DetailView):
    model = Workout
    template_name = "WorkoutAppWebGUI/workout_detail.html"
    login_url = 'login/'
    redirect_field_name = ''

    def get_queryset(self):
        query_set = super(WorkoutView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        return query_set

    def get_context_data(self, **kwargs):
        context = super(WorkoutView, self).get_context_data(**kwargs)
        context['data'] = Workout.objects.get(workout_id=self.kwargs['pk']).set_set.all()
        return context


class AddWorkoutView(LoginRequiredMixin, generic.CreateView):
    model = Workout
    form_class = WorkoutForm
    template_name = 'WorkoutAppWebGUI/add_workout.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_form(self, form_class=None):
        form = super(AddWorkoutView, self).get_form(form_class)
        form.fields['date'].input_formats = ['%d/%m/%Y']
        form.fields['date'].initial = datetime.strftime(datetime.today(), '%d/%m/%Y')
        return form

    def get_context_data(self, **kwargs):
        data = super(AddWorkoutView, self).get_context_data(**kwargs)
        data['day'] = ProgramDay.objects.filter(program_day_id=self.kwargs['day_id']).first()
        day = ExpectedSet.objects.filter(day_id=self.kwargs['day_id']).all()
        if self.request.POST:
            data['sets'] = SetFormSet(self.request.POST)
        else:
            pred = Predictor(day, self.request.user.wauser.pk)
            suggestion = pred.predict()
            data['sets'] = SetFormSet(initial=suggestion)
            data['sets'].extra = len(suggestion)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        sets = context['sets']
        form = context['form']
        if form.is_valid():
            instance = form.save(commit=False)
            instance.complete = 1
            instance.user_id = self.request.user.wauser.pk
            instance.expected = context['day']
            instance.save()
            i = 1
            old_exercise = 0
            for set_instance in sets:
                if set_instance.is_valid():
                    ex_set = set_instance.save(commit=False)
                    if ex_set.reps == 0:
                        continue
                    current_ex = ex_set.exercise_id
                    if old_exercise != current_ex:
                        i = 1
                    ex_set.set_number = i
                    ex_set.workout_id = instance.pk
                    ex_set.unit = UnitType.objects.filter(label='lbs').first()
                    ex_set.save()
                    old_exercise = current_ex
                    i += 1
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('landing')


class CreateProgramView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Program
    fields = ['program_name']
    template_name = 'WorkoutAppWebGUI/add_program.html'
    login_url = 'login/'
    redirect_field_name = ''

    def test_func(self):
        return self.request.user.groups.all()[0].name == 'trainer'

    def get_success_url(self):
        return reverse('program_day_list', kwargs={'pk': self.object.pk})


class ProgramListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = Program
    template_name = 'WorkoutAppWebGUI/program_list.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_queryset(self):
        if not self.request.user.groups.all()[0].name == 'trainer':
            queryset = super(ProgramListView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        else:
            queryset = super(ProgramListView, self).get_queryset().all()

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProgramListView, self).get_context_data()
        context['program_list'] = Program.objects.all()
        return context

    def test_func(self):
        return self.request.user.groups.all()[0].name == 'trainer'


class ProgramDayListView(LoginRequiredMixin, generic.ListView):
    model = ProgramDay
    template_name = 'WorkoutAppWebGUI/program_day_list.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_queryset(self):
        if not self.request.user.groups.all()[0].name == 'trainer':
            queryset = super(ProgramDayListView, self).get_queryset().filter(user_id=self.request.user.wauser.pk)
        else:
            queryset = super(ProgramDayListView, self).get_queryset().all()
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProgramDayListView, self).get_context_data(**kwargs)
        program = Program.objects.filter(program_id=self.kwargs['pk']).first()
        context['program'] = program
        context['days'] = ProgramDay.objects.filter(program_id=self.kwargs['pk']).all()
        return context

    def test_func(self):
        return self.request.user.groups.all()[0].name == 'trainer'


class ProgramDayDetailView(LoginRequiredMixin, generic.DetailView):
    model = ProgramDay
    template_name = 'WorkoutAppWebGUI/day_detail.html'
    login_url = 'login/'
    redirect_field_name = ''

    def get_context_data(self, **kwargs):
        context = super(ProgramDayDetailView, self).get_context_data(**kwargs)
        context['set_list'] = ExpectedSet.objects.filter(day_id=self.kwargs['pk'])
        day = ProgramDay.objects.filter(program_day_id=self.kwargs['pk']).values('day_name').first()
        context['day_name'] = day['day_name']
        return context


class ProgramDayUpdate(LoginRequiredMixin, UserPassesTestMixin,generic.UpdateView):
    model = ProgramDay
    form_class = ProgramDayForm
    template_name = 'WorkoutAppWebGUI/create_day.html'
    login_url = 'login/'
    redirect_field_name = ''

    def test_func(self):
        return self.request.user.groups.all()[0].name == 'trainer'

    def get_context_data(self, **kwargs):
        context = super(ProgramDayUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            context['sets'] = ExpectedSetFormset(self.request.POST, instance=self.object)
        else:
            context['sets'] = ExpectedSetFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        sets = context['sets']
        form = context['form']

        if form.is_valid():
            instance = form.save(commit=False)
            sets.instance = instance
            i = 1
            old_exercise = 0
            for set_instance in sets:
                if set_instance.is_valid():
                    ex_set = set_instance.save(commit=False)
                    if ex_set.exercise_id is None:
                        continue
                    current_ex = ex_set.exercise_id
                    if old_exercise != current_ex:
                        i = 1

                    ex_set.set_num = i
                    ex_set.day_id = instance.pk
                    ex_set.save()
                    old_exercise = current_ex
                    i += 1
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('program_list')


class ProgramDayCreate(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = ProgramDay
    form_class = ProgramDayForm
    template_name = 'WorkoutAppWebGUI/create_day.html'
    login_url = 'login/'
    redirect_field_name = ''

    def test_func(self):
        return self.request.user.groups.all()[0].name == 'trainer'

    def get_context_data(self, **kwargs):
        context = super(ProgramDayCreate, self).get_context_data(**kwargs)
        context['program'] = Program.objects.filter(pk=self.kwargs['program_id']).first()
        if self.request.POST:
            context['sets'] = ExpectedSetFormset(self.request.POST)
        else:
            context['sets'] = ExpectedSetFormset()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        sets = context['sets']
        form = context['form']

        if form.is_valid():
            instance = form.save(commit=False)
            instance.program = context['program']
            instance.save()
            sets.instance = instance
            i = 1
            old_exercise = 0
            for set_instance in sets:
                if set_instance.is_valid():
                    ex_set = set_instance.save(commit=False)
                    if ex_set.exercise_id is None:
                        continue
                    current_ex = ex_set.exercise_id
                    if old_exercise != current_ex:
                        i = 1

                    ex_set.set_num = i
                    ex_set.day_id = instance.pk
                    ex_set.save()
                    old_exercise = current_ex
                    i += 1
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('program_day_list', kwargs={'pk': self.kwargs['program_id']})

