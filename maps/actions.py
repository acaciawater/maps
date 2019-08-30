'''
Created on Aug 28, 2019

@author: theo
'''
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

def update_mirror(modeladmin, request, queryset):
    numLayers = 0
    numServers = 0
    for mirror in queryset:
        numLayers += mirror.update_layers()
        numServers += 1
    messages.success(request, _('{} servers processed.').format(numServers))
    messages.success(request, _('{} layers discovered.').format(numLayers))
update_mirror.short_description=_('update layer list of selected mirrors')

