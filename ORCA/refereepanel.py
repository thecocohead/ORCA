from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q, Case, When, Value, CharField
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from datetime import timedelta
import random

from ORCA.forms import TeamForm, SignUpForm, AdminRegistrationForm
from ORCA.models import Event, Team, Match, MatchBlock, ScoreSheet


@login_required(login_url="/accounts/login/")
def mainView(request, season, code):
    data = {}
    data['event'] = Event.objects.get(season=season, code=code)
    return render(request, "refereePanel.html", data)