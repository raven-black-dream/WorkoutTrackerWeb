from django import forms
from django.forms.models import inlineformset_factory
from .models import WAUser, UserWeight, UserProgram, Workout, Set


class UserForm(forms.ModelForm):
    """Form for User"""
    class Meta:
        model = WAUser
        fields = ['first_name', 'last_name']


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


class ProgramForm(forms.Form):
    """
    Form for Programs
    """
    program_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": "Program Name"}
        ),
        required=True
    )


class DayForm(forms.Form):
    """Form for Program Days"""
    day_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={'placeholder': "Day Name"}
        ),
        required=True
    )


class DaySelectorForm(forms.Form):
    """This form  is for the Record a workout function. Selects the day of the program to display"""
    day_selector = forms.ChoiceField()


SetFormSet = inlineformset_factory(
    Workout, Set, fields=('set_number', 'exercise', 'reps', 'weight', 'rpe',)
)