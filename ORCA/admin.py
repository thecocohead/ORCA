from django.contrib import admin
from ORCA.models import *

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'season', 'code', 'contact', 'startDate', 'endDate', 'location')
    pass

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'contact')
    pass

@admin.register(MatchBlock)
class MatchBlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'startTime', 'matchCount', 'timeBetweenMatches', 'order')
    list_filter = ('event',)
    pass

@admin.register(Match)
class Match(admin.ModelAdmin):
    list_display = ('id', 'event', 'phase', 'number', 'scheduledStartTime')
    pass

@admin.register(ScoreSheet)
class ScoreSheetAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'artifacts', 'minorFouls', 'majorFouls')
    pass

