from django.db import models
from django.contrib.auth.models import User


class ExerciseType(models.Model):
    exercise_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)

    class Meta:
        db_table = 'exercise_type'

    def __str__(self):
        return self.name


class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_name = models.CharField(unique=True, max_length=45)

    class Meta:
        db_table = 'program'

    def __str__(self):
        return self.program_name


class ProgramDay(models.Model):
    program_day_id = models.AutoField(primary_key=True)
    day_name = models.CharField(max_length=45)
    program = models.ForeignKey(Program, models.DO_NOTHING)

    class Meta:
        db_table = 'program_day'

    def __str__(self):
        return self.day_name


class ExpectedSet(models.Model):
    exp_set_id = models.AutoField(primary_key=True)
    day = models.ForeignKey('ProgramDay', models.DO_NOTHING)
    exercise = models.ForeignKey(ExerciseType, models.DO_NOTHING)
    set_num = models.IntegerField()
    reps_min = models.IntegerField()
    rpe = models.DecimalField(max_digits=10, decimal_places=0)
    reps_max = models.IntegerField(blank=True, null=True)
    amrap = models.BooleanField()

    class Meta:
        db_table = 'expected_set'


class Set(models.Model):
    set_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(ExerciseType, models.DO_NOTHING)
    workout = models.ForeignKey('Workout', models.DO_NOTHING)
    reps = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=0)
    rpe = models.DecimalField(max_digits=10, decimal_places=0)
    set_number = models.IntegerField()
    unit = models.ForeignKey('UnitType', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'set'


class UnitType(models.Model):
    unit_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=45)

    class Meta:
        db_table = 'unit_type'

    def __str__(self):
        return self.label


class WAUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class UserProgram(models.Model):
    user_program_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(WAUser, models.DO_NOTHING)
    program = models.ForeignKey(Program, models.DO_NOTHING, blank=True, null=True)
    current = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'user_program'


class UserWeight(models.Model):
    weight_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(WAUser, models.DO_NOTHING)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    seq_num = models.IntegerField()
    weight_unit = models.ForeignKey(UnitType, models.DO_NOTHING)
    date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_weight'

    def __str__(self):
        return f'{self.weight} {self.weight_unit.label}'


class Workout(models.Model):
    workout_id = models.AutoField(primary_key=True)
    date = models.DateTimeField(blank=True, null=True)
    complete = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(WAUser, models.DO_NOTHING)
    expected = models.ForeignKey(ProgramDay, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'workout'
