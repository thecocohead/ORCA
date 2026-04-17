from django import forms
from django.contrib.auth.forms import UserCreationForm

from ORCA.models import *

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'location')

class SignUpForm(UserCreationForm):
    email = forms.EmailField()

class AdminRegistrationForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ("teams",)