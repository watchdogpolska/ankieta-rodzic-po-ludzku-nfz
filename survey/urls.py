# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/$',
        views.SurveyDispatchView.as_view(),
        name="list"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/~print$',
        views.SurveyPrintDispatchView.as_view(),
        name="print"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/~accept$',
        views.SurveyAcceptView.as_view(),
        name="accept"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/hospital-(?P<hospital>[\d-]+)/$',
        views.HospitalSurveyView.as_view(),
        name="survey"),
    url(r'^(?P<participant>[\d-]+)/(?P<password>[\d-]+)/question-(?P<question>[\d-]+)/$',
        views.QuestionSurveyView.as_view(),
        name="survey"),

]
