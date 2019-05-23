from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Map, Layer
from maps.models import Project, Timeseries

@register(Layer)
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    list_display = ('layer','minzoom','maxzoom','opacity','map','visible')
        
class LayerInline(admin.TabularInline):
    model = Layer
    list_display = ('layer', 'visible')
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
   