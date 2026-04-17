"""
URL configuration for ORCA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from ORCA import views, refereepanel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', views.signup, name='signup'),
    path('', views.index, name='index'),
    path('events/', views.events, name='events'),
    path('event/<int:season>/<str:code>', views.event, name='event'),
    path('teams/', views.teams, name='teams'),
    path('team/<int:team>', views.team, name='team'),
    path('request/team/', views.teamRequest, name='teamRequest'),
    path('request/event/<int:id>/team/<int:team>/<str:action>', views.eventRequest, name='teamRequest'),

    path('event/<int:season>/<str:code>/admin', views.eventAdmin, name='eventAdmin'),
path('event/<int:season>/<str:code>/admin/teams', views.eventAdminRegistrations, name='eventAdmin'),
    path('event/<int:season>/<str:code>/admin/schedule', views.eventScheduleGeneration, name='eventAdmin'),
    path('event/<int:season>/<str:code>/admin/add-block', views.eventScheduleAddBlock, name='eventScheduleAddBlock'),
    path('event/<int:season>/<str:code>/admin/delete-block/<int:block_id>', views.eventScheduleDeleteBlock, name='eventScheduleDeleteBlock'),
    path('event/<int:season>/<str:code>/admin/generate', views.eventScheduleGenerate, name='eventScheduleGenerate'),

    path('event/<int:season>/<str:code>/schedule', views.eventSchedule, name='eventSchedule'),
    path('event/<int:season>/<str:code>/admin/schedule/delete', views.eventScheduleDelete, name='eventScheduleDelete'),

path('event/<int:season>/<str:code>/referee', refereepanel.mainView, name='refereePanel'),
path('event/<int:season>/<str:code>/field', views.fieldDisplay, name='fieldDisplay'),

path('event/<int:season>/<str:code>/admin/lock', views.eventAdminLock, name='eventAdmin')
]
