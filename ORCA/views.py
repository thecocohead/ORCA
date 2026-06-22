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


def index(request):
    data = {}
    data['pageTitle'] = ""
    data['authenticated'] = False
    data['username'] = ""
    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        data['events'] = Event.objects.filter(
            Q(contact=user) |
            Q(admins=user) |
            Q(referees=user) |
            Q(teams__contact=user)
        ).annotate(
            reason=Case(
                When(contact=user, then=Value('Primary Contact')),
                When(admins=user, then=Value('Event Administrator')),
                When(referees=user, then=Value('Event Referee')),
                When(teams__contact=user, then=Value('Team Contact')),
                default=Value('Other'),
                output_field=CharField(),
            )
        ).distinct()
        data['teams'] = Team.objects.filter(contact=user)
        data['authenticated'] = True
        data['username'] = user.username
    return render(request, template_name= "index.html", context=data)

def signup(request):
    if request.method == "GET":
        data = {}
        data['form'] = SignUpForm()
        data['pageTitle'] = "Sign Up"
        return render(request, "registration/signup.html", context=data)
    if request.method == "POST":
        data = {}
        data['form'] = SignUpForm(request.POST)
        if data['form'].is_valid():
            newUser = data['form'].save(commit=False)
            newUser.save()
            login(request, newUser)
            return redirect("index")
        else:
            return render(request, "registration/signup.html", context=data)

def events(request):
    data = {}
    data['events'] = Event.objects.all()
    data['pageTitle'] = "All Events"
    return render(request, template_name= "events.html", context=data)

def event(request, season, code):
    listing = Event.objects.get(season=season, code=code)
    currentUser = request.user
    #TODO: Implement error checking for bad event
    data = {}
    data['event'] = listing
    data['teams'] = listing.teams.all().order_by('number')
    data['pageTitle'] = listing.name

    isAdmin = False
    isReferee = False
    if currentUser.is_authenticated:
        isAdmin = listing.admins.filter(pk=currentUser.pk).exists()
        isReferee = listing.referees.filter(pk=currentUser.pk).exists()

    data['isAdmin'] = isAdmin
    data['isReferee'] = isReferee

    if listing.startDate == listing.endDate:
        data['multiDay'] = False
    else:
        data['multiDay'] = True

    return render(request, template_name= "event.html", context=data)

def eventSchedule(request, season, code):
    event = Event.objects.get(season=season, code=code)
    data = {}
    data['event'] = event
    data['matches'] = event.match_set.all()
    data['pageTitle'] = str(event.season) + event.code + " Schedule"

    for match in data['matches']:
        redScoreSheet = match.redScoreSheet
        blueScoreSheet = match.blueScoreSheet
        if redScoreSheet is not None and blueScoreSheet is not None:
            # both score sheets exist
            redScore = redScoreSheet.artifacts * 1 + redScoreSheet.minorFouls * -3 + redScoreSheet.majorFouls * -5
            blueScore = blueScoreSheet.artifacts * 1 + blueScoreSheet.minorFouls * -3 + blueScoreSheet.majorFouls * -5
            match.redScore = redScore
            match.blueScore = blueScore
            if redScore > blueScore:
                match.redWin = True
            elif blueScore > redScore:
                match.blueWin = True


    return render(request, template_name= "eventSchedule.html", context=data)



def teams(request):
    data = {}
    data['teams'] = Team.objects.all()
    data['pageTitle'] = "Team Listing"
    return render(request, template_name="teams.html", context=data)


def team(request, team):
    data = {}
    team = Team.objects.get(id=team)
    events = team.event_teams.all().order_by('startDate')
    if request.user.is_authenticated and request.user == team.contact:
        data['availableEvents'] = Event.objects.exclude(teams=team).exclude(registrationLocked=True).order_by('startDate')
        data['isAdmin'] = True
    else:
        data['availableEvents'] = []
    data['team'] = team
    data['events'] = events
    data['pageTitle'] = "Team " + str(team.number)
    return render(request, template_name="team.html", context=data)

@login_required(login_url="/accounts/login/")
def teamRequest(request):
    if request.method == "GET":
        data = {}
        data['form'] = TeamForm()
        data['pageTitle'] = "New Team Request"
        return render(request, template_name="teamrequest.html", context=data)
    if request.method == "POST":
        data = {}
        data['form'] = TeamForm(request.POST)
        if data['form'].is_valid():
            newTeam = data['form'].save(commit=False)
            newTeam.contact = request.user
            newTeam.save()
            return HttpResponseRedirect("/team/" + str(newTeam.id))
        else:
            return render(request, template_name="teamrequest.html", context=data)

@login_required(login_url="/accounts/login/")
def eventRequest(request, id, team, action):
    event = Event.objects.get(pk=id)
    team = Team.objects.get(id=team)
    if request.user != team.contact:
        return HttpResponseNotAllowed("You are not the team admin")
    if event.registrationLocked:
        return HttpResponseNotAllowed("Registration is currently locked for this event.")
    if action == "register":
        event.teams.add(team)
        event.save()
        return HttpResponseRedirect("/event/" + str(event.season) + "/" + str(event.code))
    elif action == "drop":
        event.teams.remove(team)
        event.save()
        return HttpResponseRedirect("/team/" + str(team.id))
    else:
        return HttpResponseBadRequest("Invalid Request")


@login_required(login_url="/accounts/login/")
def eventAdmin(request, season, code):
    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")
    data = {}
    data['event'] = event
    data['matches'] = event.match_set.all()
    data['pageTitle'] = str(event.season) + event.code + " Admin Panel"
    return render(request, template_name="adminPanel.html", context=data)

@login_required(login_url="/accounts/login/")
def eventAdminLock(request, season, code):
    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")
    event.registrationLocked = not event.registrationLocked
    event.save()
    return HttpResponseRedirect("/event/" + str(event.season) + "/" + str(event.code) + "/admin")


@login_required(login_url="/accounts/login/")
def eventAdminRegistrations(request, season, code):
    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")

    if request.method == "POST":
        form = AdminRegistrationForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/event/" + str(event.season) + "/" + str(event.code) + "/admin")
    elif request.method == "GET":
        data = {}
        data['event'] = event
        data['pageTitle'] = str(event.season) + event.code + " Registration Listing"
        data['form'] = AdminRegistrationForm(instance=event)
        return render(request, template_name="admin/registrations.html", context=data)
    else:
        return HttpResponseBadRequest("Invalid Request")


def fieldDisplay(request, season, code):
    event = Event.objects.get(season=season, code=code)
    data = {}
    data['event'] = event
    return render(request, "fieldDisplay.html", data)

# ai stuff

@login_required(login_url="/accounts/login/")
def eventScheduleGeneration(request, season, code):
    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")

    if request.method == "GET":
        data = {}
        data['event'] = event
        data['pageTitle'] = str(event.season) + event.code + " Schedule Generation"
        data['teams'] = event.teams.all()
        data['matchBlocks'] = MatchBlock.objects.filter(event=event).order_by('order', 'startTime')

        # Calculate total match capacity from blocks
        total_capacity = sum(block.matchCount for block in data['matchBlocks'])
        data['totalCapacity'] = total_capacity

        return render(request, template_name="admin/schedule.html", context=data)

@login_required(login_url="/accounts/login/")
def eventScheduleDelete(request, season, code):
    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")
    matches = Match.objects.filter(event=event)
    matches.delete()
    return HttpResponseRedirect("/event/" + str(event.season) + "/" + str(event.code) + "/admin")


@login_required(login_url="/accounts/login/")
def eventScheduleAddBlock(request, season, code):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid Request Method'})

    try:
        event = Event.objects.get(season=season, code=code)
    except Event.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Event not found'})

    if not event.admins.filter(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'})

    try:
        from datetime import datetime

        start_time_str = request.POST.get('startTime')
        match_count = int(request.POST.get('matchCount'))
        time_between = int(request.POST.get('timeBetween'))

        # Parse the datetime string from HTML5 datetime-local input
        # Format is: "2026-02-27T10:00"
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')

        # Get the highest order number and add 1
        max_order = MatchBlock.objects.filter(event=event).count()

        block = MatchBlock.objects.create(
            event=event,
            startTime=start_time,
            matchCount=match_count,
            timeBetweenMatches=time_between,
            order=max_order
        )

        return JsonResponse({
            'success': True,
            'block': {
                'id': block.id,
                'startTime': block.startTime.strftime('%Y-%m-%d %H:%M'),
                'matchCount': block.matchCount,
                'timeBetween': block.timeBetweenMatches,
                'endTime': block.get_end_time().strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@login_required(login_url="/accounts/login/")
def eventScheduleDeleteBlock(request, season, code, block_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Invalid Request Method'})

    try:
        event = Event.objects.get(season=season, code=code)
    except Event.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Event not found'})

    if not event.admins.filter(pk=request.user.pk).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'})

    try:
        block = MatchBlock.objects.get(id=block_id, event=event)
        block.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@login_required(login_url="/accounts/login/")
def eventScheduleGenerate(request, season, code):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid Request")

    event = Event.objects.get(season=season, code=code)
    if not event.admins.filter(pk=request.user.pk).exists():
        return HttpResponseNotAllowed("You are not allowed to view this page.")

    try:
        matches_per_team = int(request.POST.get('matchesPerTeam'))
        phase = request.POST.get('phase', 'Qualification')

        # Get all teams and blocks
        teams = list(event.teams.all())
        blocks = MatchBlock.objects.filter(event=event).order_by('order', 'startTime')

        if len(teams) < 4:
            return JsonResponse({'success': False, 'error': 'Need at least 4 teams to generate schedule'})

        # Calculate required matches
        required_matches = (len(teams) * matches_per_team) // 4
        total_capacity = sum(block.matchCount for block in blocks)

        if total_capacity < required_matches:
            return JsonResponse({
                'success': False,
                'error': f'Not enough match blocks. Need {required_matches} matches, have capacity for {total_capacity}'
            })

        # Delete existing matches for this event and phase
        Match.objects.filter(event=event, phase=phase).delete()

        # Generate schedule using round-robin with randomization
        matches = []
        team_match_counts = {team.number: 0 for team in teams}

        match_number = 1
        current_block_idx = 0
        current_block = blocks[current_block_idx]
        current_block_match = 0
        current_time = current_block.startTime

        # Try to create matches until we hit the target
        attempts = 0
        max_attempts = required_matches * 10

        while match_number <= required_matches and attempts < max_attempts:
            attempts += 1

            # Find teams that need more matches
            available_teams = [t for t in teams if team_match_counts[t.number] < matches_per_team]

            if len(available_teams) < 4:
                break

            # Randomly select 4 teams
            selected = random.sample(available_teams, 4)

            # blank scoresheets


            # Create match
            match = Match(
                event=event,
                phase=phase,
                number=match_number,
                scheduledStartTime=current_time,
                red1=selected[0],
                red2=selected[1],
                blue1=selected[2],
                blue2=selected[3],
                blueScoreSheet=None,
                redScoreSheet=None,
            )
            match.save()

            # Update counts
            for team in selected:
                team_match_counts[team.number] += 1

            match_number += 1
            current_block_match += 1

            # Move to next time slot or block
            if current_block_match >= current_block.matchCount:
                current_block_idx += 1
                if current_block_idx >= len(blocks):
                    break
                current_block = blocks[current_block_idx]
                current_block_match = 0
                current_time = current_block.startTime
            else:
                current_time += timedelta(minutes=current_block.timeBetweenMatches)

        return JsonResponse({
            'success': True,
            'matchesCreated': match_number - 1,
            'message': f'Successfully generated {match_number - 1} matches'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
