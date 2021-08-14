from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext as _
from .models import WAUser, UserWeight, UserProgram, Workout, Set, Program, ProgramDay, ExpectedSet, ExerciseType
from .models import Prediction
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
        fields = ['username', 'first_name', 'last_name']


class ExerciseForm(forms.ModelForm):
    """Form for ExerciseType"""
    class Meta:
        model = ExerciseType
        fields = ['name', 'weighted', 'weight_step']


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


class PredictionValidationForm(forms.ModelForm):
    """Form for Validating Prediction"""
    class Meta:
        model = Workout
        fields = ['expected', 'date']

    def __init__(self, *args, **kwargs):
        super(PredictionValidationForm, self).__init__(*args, **kwargs)
        self.fields['expected'].disabled = True
        self.fields['date'].disabled = True
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 create-label'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Div(
                Fieldset('Workout', 'expected', 'date'),
                Fieldset('Predictions',
                         Formset('predictions')),
                HTML('<br>'),
                ButtonHolder(Submit('submit', 'save'))
            )
        )


class PredictionForm(forms.ModelForm):
    user_suggestion = forms.IntegerField(min_value=-1, max_value=1, required=False, label='Suggestion')

    class Meta:
        model = Prediction
        fields = ['exercise', 'avg_reps', 'avg_rpe', 'recommendation', 'user_agrees', 'user_suggestion']
        labels = {'user_agrees': 'Agree?'}

    def __init__(self, *args, **kwargs):
        super(PredictionForm, self).__init__(*args, **kwargs)
        self.fields['exercise'].disabled = True
        self.fields['avg_reps'].disabled = True
        self.fields['avg_rpe'].disabled = True
        self.fields['user_agrees'].required = True
        self.fields['recommendation'].disabled = True

    def clean(self):
        data = super().clean()
        agree = data.get('user_agrees')
        suggestion = data.get('user_suggestion')

        if not agree and suggestion is None:
            self.add_error('user_suggestion', _('Cannot be empty if you disagree'))
        return data


SetFormSet = inlineformset_factory(
    Workout, Set, fields=('exercise', 'reps', 'weight', 'rpe',), can_delete=False
)

ExpectedSetFormset = inlineformset_factory(
    ProgramDay, ExpectedSet, fields=('exercise', 'reps_min', 'reps_max', 'amrap', 'rpe'), extra=30, can_delete=False
)

PredictionFormSet = inlineformset_factory(
    Workout,
    Prediction,
    form=PredictionForm,
    extra=0,
    can_delete=False
)
