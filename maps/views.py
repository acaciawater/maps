'''
Created on May 15, 2019

@author: theo
'''
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse, HttpResponseNotFound,\
    JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from .models import Map, Project, UserConfig
from maps.models import DocumentGroup, Document


class MapDetailView(LoginRequiredMixin, DetailView):
    ''' View with leaflet map, legend and layer list '''
    model = Map

    def get_map(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = {'zoom': 12, 'center': [52, 5]}
        map_object = self.get_map()
        context['map'] = map_object
        context['extent'] = map_object.extent()
        return context


class ProjectDetailView(MapDetailView):
    ''' ModelView with link to remote meetnet app with monitoring locations and timeseries '''
    model = Project

    def get_map(self):
        return self.get_object().map

    def get_context_data(self, **kwargs):
        context = MapDetailView.get_context_data(self, **kwargs)
        project = self.get_object()
        if project.timeseries:
            series = project.timeseries
            context['series'] = json.dumps({
                'server': series.server, 'items': series.locations,
                'popup': series.popup, 'chart': series.chart
            })
        return context


@csrf_exempt
@login_required
def reorder(request, pk):
    ''' reorder layers in map and save to user config
        request.body contains names of layers as json array in proper order
        is something like ["suitability","ndvi",,...]
    '''
    if not request.user.is_authenticated:
        return HttpResponse('Authentication required to reorder layers.', status=401)

    user = request.user
    target = get_object_or_404(Map, pk=pk)
    items = json.loads(request.body.decode('utf-8'))

    # make sure user config is in sync with map
    UserConfig.sync(user, target)

    for index, item in enumerate(items):
        config = user.userconfig_set.get(
            layer__map=target, layer__layer__title=item)
        if config.order != index:
            config.order = index
            config.save(update_fields=('order',))

    return HttpResponse(status=200)


@csrf_exempt
@login_required
def toggle(request, pk):
    ''' toggle visibility of layers in map and save to user config
        request.body contains names of layers as json array in proper order
        is something like ["suitability","ndvi",,...]
    '''
    if not request.user.is_authenticated:
        return HttpResponse('Authentication required to toggle visibility of layers.', status=401)

    user = request.user
    target = get_object_or_404(Map, pk=pk)
    items = json.loads(request.body.decode('utf-8'))

    # make sure user config is in sync with map
    UserConfig.sync(user, target)

    for item in items:
        config = user.userconfig_set.get(
            layer__map=target, layer__layer__title=item)
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
    if not cluster:
        return HttpResponseNotFound('Cluster name or number is missing.')
    clustername = CLUSTERS[cluster] if cluster in '12345678' else cluster
    map_object = get_object_or_404(Map, name__icontains=clustername)
    return redirect('map-detail', pk=map_object.pk)


@login_required
def get_map_config(request, pk):
    ''' return user's layer configuration for all groups in the map '''
    map_object = get_object_or_404(Map, pk=pk)
    user = request.user
    UserConfig.sync(user, map_object)
    return HttpResponse(UserConfig.groups(user, map_object), content_type='application/json')


def docs2json(request):
    ''' return json response with all documents grouped by theme '''
    
    def process_group(group, result):
        data = {
            'id': group.id,
            'name': group.name,
            'documents': process_docs(group),
            'folders': []
        }
        result.append(data)
        for child in group.documentgroup_set.all():
            process_group(child, data['folders'])

    def process_docs(group):
        result = []
        for doc in group.document_set.order_by('cluster'):
            result.append({
                'id': doc.id,
                'name': doc.name,
                'description': doc.description,
                'url': doc.url
                })
        return result
    
    root = DocumentGroup.objects.get(parent__isnull=True)
    result = []
    process_group(root, result)
    return JsonResponse({'results': result})

def clus2json(request):
    ''' return json response with documents grouped by cluster '''
    result = []
    for cluster in range(1,9):
        key = str(cluster)
        name = CLUSTERS.get(key,f'Cluster{key}')
        data = {'cluster': cluster, 'name': name, 'documents': [], 'folders': []}
        docs = Document.objects.filter(cluster=cluster)
        for group in docs.values_list('group__name',flat=True).distinct():
            # group ends with Maps or Models. Strip the last s
            tag = group[:-1] if group.endswith('s') else group
            items = [{'id': doc.id,
                      'name': f'{tag} of {doc.name}',
                      'description': doc.description,
                      'url': doc.url
                      } 
                    for doc in docs.filter(group__name=group)]
            data['folders'].append({'name': group, 'folders':[], 'documents': items})
        result.append(data)
    return JsonResponse({'results':  [{'folders': result}] })

def docs2tree(request):
    ''' return json response for treeview '''
    
    def process_group(group, result):
        data = {
            'text': group.name,
            'nodes': process_docs(group),
        }
        result.append(data)
        for child in group.documentgroup_set.all():
            process_group(child, data['nodes'])

    def process_docs(group):
        result = []
        for doc in group.document_set.all():
            result.append({
                'text': doc.name,
                'href': doc.url
                })
        return result
    
    root = DocumentGroup.objects.get(parent__isnull=True)
    result = []
    process_group(root, result)
    return JsonResponse({'tree': result})
