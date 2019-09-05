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

def reorder1(request, pk):
    ''' reorder layers in map
        request.body result of jQuery.sortable('serialize') 
        is something like b'item=1&item=2....'
    '''
    mapObject = get_object_or_404(Map,pk=pk)
    items = request.body.decode('utf-8').split('&')
    order = map(lambda item: int(item.split('=')[1]), items)
    layers = list(mapObject.layer_set.order_by('order'))
    for index, item in enumerate(order):
        layer = layers[item-1]
        if layer.order != index:
            layer.order = index
            layer.save(update_fields=('order',))
    return HttpResponse(status=200)

def reorder(request, pk):
    ''' reorder layers in map
        request.body contains names of layers as json array in proper order 
        is something like ["suitability","ndvi",,...]
    '''
    mapObject = get_object_or_404(Map,pk=pk)
    items = json.loads(request.body)
    for index, item in enumerate(items):
        layer = mapObject.layer_set.get(layer__title=item)
        if layer.order != index:
            layer.order = index
            layer.save(update_fields=('order',))
    return HttpResponse(status=200)

def toggle(request, pk):
    ''' toggle visibility of layers in map
        request.body contains names of layers as json array in proper order 
        is something like ["suitability","ndvi",,...]
    '''
    mapObject = get_object_or_404(Map,pk=pk)
    items = json.loads(request.body)
    for item in items:
        layer = mapObject.layer_set.get(layer__title=item)
        layer.visible = not layer.visible
        layer.save(update_fields=('visible',))
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