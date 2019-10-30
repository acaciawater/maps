'''
Created on Aug 28, 2019

@author: theo
'''
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages


def update_mirror(_modeladmin, request, queryset):
    '''
    updates layer list of mirror map
    '''
    num_layers = 0
    num_servers = 0
    for mirror in queryset:
        num_layers += mirror.update_layers()
        num_servers += 1
    messages.success(request, _('{} servers processed.').format(num_servers))
    messages.success(request, _('{} layers discovered.').format(num_layers))


update_mirror.short_description = _('update layer list of selected mirrors')
