from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=200)
    number = models.IntegerField(default=-1)
    location = models.CharField(max_length=200)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    season = models.IntegerField()
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    startDate = models.DateField()
    endDate = models.DateField()
    location = models.CharField(max_length=200)
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='event_admins', blank=True)
    referees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='event_referees', blank=True)
    teams = models.ManyToManyField(Team, related_name='event_teams', blank=True)
    registrationLocked = models.BooleanField(default=False)

    def __str__(self):
        return str(self.season) + self.code

class Match(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    phase = models.CharField(max_length=50)
    number = models.IntegerField()
    scheduledStartTime = models.DateTimeField()
    status = models.CharField(max_length=50, default="Scheduled")
    red1 = models.ForeignKey(Team, related_name="match_red1", on_delete=models.PROTECT)
    red2 = models.ForeignKey(Team, related_name="match_red2",  on_delete=models.PROTECT)
    blue1 = models.ForeignKey(Team, related_name="match_blue1",  on_delete=models.PROTECT)
    blue2 = models.ForeignKey(Team, related_name="match_blue2",  on_delete=models.PROTECT)
    redScoreSheet = models.ForeignKey('scoreSheet', related_name="red_scoreSheet", on_delete=models.CASCADE, null=True)
    blueScoreSheet = models.ForeignKey('scoreSheet', related_name="blue_scoreSheet", on_delete=models.CASCADE, null=True)


class MatchBlock(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    startTime = models.DateTimeField()
    matchCount = models.IntegerField()
    timeBetweenMatches = models.IntegerField(help_text="Time between matches in minutes")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'startTime']

    def get_end_time(self):
        from datetime import timedelta
        if self.matchCount > 0:
            total_minutes = (self.matchCount - 1) * self.timeBetweenMatches
            return self.startTime + timedelta(minutes=total_minutes)
        return self.startTime

class ScoreSheet(models.Model):
    id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    artifacts = models.IntegerField()
    team1endgame = models.IntegerField()
    team2endgame = models.IntegerField()
    minorFouls = models.IntegerField()
    majorFouls = models.IntegerField()
