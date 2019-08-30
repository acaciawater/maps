from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Map, Layer
from django.contrib import messages
from maps.models import Project, Timeseries, Group, Mirror
from maps.actions import update_mirror
from maps.forms import LayerPropertiesForm
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

@register(Group)
class GroupAdmin(admin.ModelAdmin):
    model = Group
    fields = (('name','map'),('layers',))
    list_display = ('name', 'map', 'layer_count')
    list_filter = ('map',)
    filter_horizontal = ('layers',)
    

@register(Layer)
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    fields = (('layer','map'),('groups',),
              ('order','visible','use_extent'),
              ('opacity','transparent'),
              ('minzoom','maxzoom'),
              ('properties','clickable'),
              'stylesheet',
              ('download_url','allow_download'),
              )
    list_filter = ('visible','map','groups','layer__server','allow_download')
    list_display = ('layer','map','group_names','extent','use_extent')
    search_fields = ('layer__title',)
    filter_horizontal = ('groups',)
    actions = ['update_layer_properties']
    
    def update_layer_properties(self, request, queryset):
        if 'apply' in request.POST:
            form = LayerPropertiesForm(request.POST)
            if form.is_valid():
                # filter null items from cleaned_data
                data = {k:v for k,v in form.cleaned_data.items() if v is not None}
                ret = queryset.update(**data)
                messages.success(request, _('Properties updated successfully for {} layers').format(ret))
            else:
                # warn about the problem
                messages.error(request, _('Properties were not updated: error in form'))
        elif 'cancel' in request.POST:
            messages.warning(request,_('Action to update layer properties was cancelled'))
        else:
            form = LayerPropertiesForm()
            return render(request, 'maps/layer_properties.html', 
                          context = {'form': form, 'meta': self.model._meta, 'queryset': queryset})

    update_layer_properties.short_description = _('Update layer properties')    
        
class LayerInline(admin.TabularInline):
    model = Layer
    fields = ('layer', 'order', 'visible', 'clickable', 'allow_download', 'opacity')
    extra = 0
    
    def get_queryset(self, request):
        return admin.TabularInline.get_queryset(self, request).order_by('order').prefetch_related('layer')
    
@register(Map)
class MapAdmin(admin.ModelAdmin):
    model = Map
    inlines = [LayerInline]
    actions = ['update_extent']
    
    def update_extent(self, request, queryset):
        count = 0
        for m in queryset:
            m.set_extent()
            count+=1
        messages.success(request, _('{} extents were updated sucessfully.').format(count))
        
@register(Mirror)
class MirrorAdmin(MapAdmin):
    model = Mirror
    actions = [update_mirror]
    
@register(Timeseries)
class TimeseriesAdmin(admin.ModelAdmin):
    model = Timeseries
    
@register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project
