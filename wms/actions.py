'''
Created on May 18, 2019

@author: theo
'''
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

def updateLayers(modeladmin, request, queryset):
    # TODO: remove layers that no longer exist on server ??
    numCreated = 0
    for server in queryset:
        for layername, details in server.layerDetails().items():
            try:
                layer, created = server.layer_set.get_or_create(layername=layername,defaults = {
                    'title': details.title or layername,
                    'attribution': details.attribution.get('title','') if hasattr(details,'attribution') else ''})
                if created:
                    numCreated += 1
            except Exception as e:
                messages.error(request, e)
    messages.success(request, _('{} new layers discovered.').format(numCreated))
updateLayers.short_description=_('update layer list of selected servers')        