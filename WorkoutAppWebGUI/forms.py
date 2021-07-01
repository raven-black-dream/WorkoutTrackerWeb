from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from .models import WAUser, UserWeight, UserProgram, Workout, Set, Program, ProgramDay, ExpectedSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Div, HTML, ButtonHolder, Submit
from .layout import *


class UserForm(forms.ModelForm):
    """Form for WAUser"""
    class Meta:
        model = WAUser
        fields = ['first_name', 'last_name']


class AddUserForm(UserCreationForm):
    """Form for User"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class UserWeightForm(forms.ModelForm):
    """Form for UserWeight"""
    class Meta:
        model = UserWeight
        fields = ['weight', "weight_unit"]


class UserProgramForm(forms.ModelForm):
    """Form for UserPrograms"""
    class Meta:
        model = UserProgram
        fields = ['program']


class DaySelectorForm(forms.Form):
    """This form  is for the Record a workout function. Selects the day of the program to display"""
    day_selector = forms.ChoiceField()


class ProgramDayForm(forms.ModelForm):
    """Form for Program Day"""
    class Meta:
        model = ProgramDay
        fields = ['day_name']
        exclude = ['pk']

    def __init__(self, *args, **kwargs):
        super(ProgramDayForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 create-label'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Div(
                Field('day_name'),
                Fieldset('Sets',
                         Formset('sets')),
                HTML('<br>'),
                ButtonHolder(Submit('submit', 'save'))
            )
        )


class WorkoutForm(forms.ModelForm):
    """Form for Program Day"""
    class Meta:
        model = Workout
        fields = ['date']

    def __init__(self, *args, **kwargs):
        super(WorkoutForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 create-label'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Div(
                Field('date'),
                Fieldset('Sets',
                         Formset('sets')),
                HTML('<br>'),
                ButtonHolder(Submit('submit', 'save'))
            )
        )


SetFormSet = inlineformset_factory(
    Workout, Set, fields=('exercise', 'reps', 'weight', 'rpe',), can_delete=False
)

ExpectedSetFormset = inlineformset_factory(
        ProgramDay, ExpectedSet, fields=('exercise', 'reps_min', 'reps_max', 'amrap', 'rpe'), extra=30, can_delete=False
)
