from django import forms
from .models import Program, WAUser, UserWeight, UserProgram


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


class ProgramSetForm(forms.Form):
    """Form for Exercise Sets within Program Days"""


