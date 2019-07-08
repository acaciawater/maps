'''
Created on May 15, 2019

@author: theo
'''
from django.views.generic.base import TemplateView
from django.conf import settings
from .models import Project, Map
from django.views.generic.detail import DetailView
import json

class MapDetailView(DetailView):
    model = Map
    
    def getMap(self):
        return self.get_object() 
     
    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = {'zoom': 12, 'center': [52,5]}
        mapObject = self.getMap()
        context['map'] = mapObject
        context['extent'] = mapObject.extent()
        return context
    
class ProjectDetailView(MapDetailView):
    model = Project

    def getMap(self):
        return self.get_object().map
    
    def get_context_data(self, **kwargs):
        context = MapDetailView.get_context_data(self, **kwargs)
        project = self.get_object()
        if project.timeseries:
            series = project.timeseries
            context['series'] = json.dumps({'server': series.server, 'items': series.locations, 'popup': series.popup, 'chart':series.chart})
        return context

