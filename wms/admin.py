from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import Server, Layer
from wms.actions import updateLayers

@register(Layer)    
class LayerAdmin(admin.ModelAdmin):
    model = Layer
    list_display = ('server','title', 'layername')
    list_filter = ('server',)

class LayerInline(admin.TabularInline):
    model = Layer
    extra = 0
    
@register(Server)    
class ServerAdmin(admin.ModelAdmin):
    model = Server
    actions = [updateLayers]
    inlines = [LayerInline]

