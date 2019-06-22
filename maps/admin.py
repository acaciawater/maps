from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Map, Layer
from maps.models import Project, Timeseries

@register(Layer)
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    fields = (('layer','map'),
              ('order','visible','use_extent'),
              ('opacity','transparent'),
              ('minzoom','maxzoom'),
              ('properties','clickable'),
              'stylesheet',
              ('download_url','allow_download'),
              )
    list_filter = ('map','layer__server','allow_download')
    list_display = ('layer','map')
        
class LayerInline(admin.TabularInline):
    model = Layer
    fields = ('layer', 'order', 'visible', 'clickable', 'allow_download', 'opacity')
    extra = 0

@register(Map)
class MapAdmin(admin.ModelAdmin):
    model = Map
    inlines = [LayerInline]
    
@register(Timeseries)
class TimeseriesAdmin(admin.ModelAdmin):
    model = Timeseries
    
@register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project
