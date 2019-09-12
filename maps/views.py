'''
Created on May 15, 2019

@author: theo
'''
from django.views.generic.base import TemplateView
from django.conf import settings
from .models import Project, Map
from django.views.generic.detail import DetailView
import json
from django.shortcuts import get_object_or_404, redirect
from django.http.response import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from maps.models import UserConfig

class MapDetailView(LoginRequiredMixin, DetailView):
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

@csrf_exempt
@login_required
def reorder(request, pk):
    ''' reorder layers in map
        request.body contains names of layers as json array in proper order 
        is something like ["suitability","ndvi",,...]
    '''
    if not request.user.is_authenticated:
        return HttpResponse('Authentication required to reorder layers.', status=401)
    
    user = request.user
    target = get_object_or_404(Map,pk=pk)
    items = json.loads(request.body.decode('utf-8'))
    # make sure user config is in sync with map
    UserConfig.sync(user, target)
    for index, item in enumerate(items):
        config = user.userconfig_set.get(layer__map=target, layer__layer__title=item)
        if config.order != index:
            config.order = index
            config.save(update_fields=('order',))
    return HttpResponse(status=200)

@csrf_exempt
@login_required
def toggle(request, pk):
    ''' toggle visibility of layers in map
        request.body contains names of layers as json array in proper order 
        is something like ["suitability","ndvi",,...]
    '''
    if not request.user.is_authenticated:
        return HttpResponse('Authentication required to toggle visibility of layers.', status=401)

    user = request.user
    target = get_object_or_404(Map,pk=pk)
    items = json.loads(request.body.decode('utf-8'))
    # make sure user config is in sync with map
    UserConfig.sync(user, target)
    for item in items:
        config = user.userconfig_set.get(layer__map=target, layer__layer__title=item)
        config.visible = not config.visible
        config.save(update_fields=('visible',))
    return HttpResponse(status=200)


class HomeView(TemplateView):
    template_name = 'gw4e.html'


CLUSTERS = {
    '1': 'Wag Himra',
    '2': 'Afar',
    '3': 'Siti',
    '4': 'Liben',
    '5': 'Bale',
    '6': 'Borena',
    '7': 'Wolayta',
    '8': 'South Omo'
}

def map_proxy(request):
    ''' resolve map id from cluster name or number '''
    cluster = request.GET.get('cluster')
    if cluster:
        if cluster in '12345678':
            clustername = CLUSTERS[cluster]
        else:
            clustername = cluster
        mapObject = get_object_or_404(Map,name__icontains=clustername)
        return redirect('map-detail',pk=mapObject.pk)
    else:
        return HttpResponseNotFound('Cluster name or number is missing.')

@login_required
def get_map_config(request, pk):
    ''' return user's layer configuration for all groups in the map '''
    map = get_object_or_404(Map,pk=pk)
    user = request.user
    UserConfig.sync(user, map)
    return HttpResponse(UserConfig.groups(user, map), content_type='application/json')
