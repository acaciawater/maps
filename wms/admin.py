from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Map, WMSServer, Layer, MapLayer, WMSLayer

@register(WMSLayer)    
class WMSLayerAdmin(admin.ModelAdmin):
    model = WMSLayer
    list_display = ('server','layername')
    list_filter = ('server',)

class WMSLayerInline(admin.TabularInline):
    model = WMSLayer
    extra = 0
    
@register(WMSServer)    
class WMSServerAdmin(admin.ModelAdmin):
    model = WMSServer
    inlines = [WMSLayerInline]

@register(Layer)
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    list_display = ('name','source','minzoom','maxzoom','opacity')
        
@register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    model = MapLayer
    list_filter = ('map',)
    list_display = ('layer','order','visible','map')
    
class MapLayerInline(admin.TabularInline):
    model = MapLayer
    list_display = ('layer','order','visible')
    extra = 0

@register(Map)
class MapAdmin(admin.ModelAdmin):
    model = Map
    inlines = [MapLayerInline]