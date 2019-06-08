'''
Created on May 15, 2019

@author: theo
'''
from django.views.generic.base import TemplateView
from django.conf import settings
from .models import Project
from django.views.generic.detail import DetailView
import json

class ProjectDetailView(DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = {'zoom': 12, 'center': [52,5]}
        project = self.get_object()
        context['extent'] = project.map.extent()
        if project.timeseries:
            series = project.timeseries
            context['urls'] = json.dumps({'server': series.server, 'items': series.locations, 'popup': series.popup, 'chart':series.chart})
        return context
