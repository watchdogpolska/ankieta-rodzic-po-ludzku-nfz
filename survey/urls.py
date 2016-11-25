# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/$',
        views.ParticipantFormView.as_view(),
        name="list"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/$',
        views.HospitalListView.as_view(),
        name="list2"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/~print$',
        views.SurveyPrintView.as_view(),
        name="print"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/(?P<hospital>[\d-]+)/$',
        views.HospitalSurveyView.as_view(),
        name="survey"),

]
