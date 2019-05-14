from rest_framework import serializers

from .models import Map, MapLayer, Layer, WMSLayer, WMSServer

class WMSServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WMSServer
        fields = ('name','url')

class WMSLayerSerializer(serializers.ModelSerializer):
    server = WMSServerSerializer()
    class Meta:
        model = WMSLayer
        fields = ('layername','server')
        
class LayerSerializer(serializers.ModelSerializer):
    source = WMSLayerSerializer()
    class Meta:
        model = Layer            
        fields =('name','source','minzoom', 'maxzoom', 'opacity')
        
class MapLayerSerializer(serializers.ModelSerializer):
    layer = LayerSerializer()
    
    class Meta:
        model = MapLayer            
        fields = ('layer','order','visible')
        
class MapSerializer(serializers.ModelSerializer):
    layers = MapLayerSerializer(many=True)
    
    class Meta:
        model = Map
        fields = ('name','layers')