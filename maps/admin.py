from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Map, Layer
from django.contrib import messages
from maps.models import Project, Timeseries, Group, Mirror
from maps.actions import update_mirror
from maps.forms import LayerPropertiesForm, SelectMapForm
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.db.models import Max

@register(Group)
class GroupAdmin(admin.ModelAdmin):
    model = Group
    fields = ('name','map')
    list_display = ('name', 'map', 'layer_count')
    list_filter = ('map',)
    

@register(Layer)
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    fields = (('layer','map','group'),
              ('order','visible','use_extent'),
              ('opacity','transparent'),
              ('minzoom','maxzoom'),
              ('properties','clickable'),
              'stylesheet',
              ('download_url','allow_download'),
              )
    list_filter = ('visible','map','group','layer__server','allow_download')
    list_display = ('layer','map','group','extent','use_extent')
    search_fields = ('layer__title',)
    actions = ['update_layer_properties','add_layers_to_map']
    
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

    def add_layers_to_map(self, request, queryset):
        if 'apply' in request.POST:
            form = SelectMapForm(request.POST)
            if form.is_valid():
                map = form.cleaned_data['map']
                if map is None:
                    messages.warning(request,_('No map was selected. Action to add layers to map was cancelled.'))
                    return
                added = 0
                skipped = 0
                order = map.layer_set.aggregate(max=Max('order'))['max'] or 0
                for layer in queryset:
                    if map.layer_set.filter(layer=layer.layer).exists():
                        skipped += 1
                    else:
                        layer.pk = None
                        layer.map = map
                        layer.order = order
                        try:
                            layer.save()
                            order += 1
                            added += 1
                        except:
                            skipped += 1
                if added:
                    messages.success(request, _('{} layers were added to map {}.').format(added,map))
                if skipped:
                    messages.warning(request, _('{} layers were not added to map {}.').format(skipped,map))
            else:
                # warn about the problem
                messages.error(request, _('No layers were added: error in form.'))
        elif 'cancel' in request.POST:
            messages.warning(request,_('Action to add layers to map was cancelled.'))
        else:
            form = SelectMapForm()
            return render(request, 'maps/add_layers.html', 
                          context = {'form': form, 'meta': self.model._meta, 'queryset': queryset})

    add_layers_to_map.short_description = _('Add selected layers to a map')    
        
class LayerInline(admin.TabularInline):
    model = Layer
    fields = ('layer', 'order', 'group', 'visible', 'clickable', 'allow_download', 'opacity')
    extra = 0
    
    def get_queryset(self, request):
        return admin.TabularInline.get_queryset(self, request).order_by('order').prefetch_related('layer')
    
@register(Map)
class MapAdmin(admin.ModelAdmin):
    model = Map
    inlines = [LayerInline]
    exclude = ['slug']
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
