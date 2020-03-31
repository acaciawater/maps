from maps.models import Map
from wms.models import Layer

def set_server(server):
    for m in Map.objects.filter(name__istartswith='cluster'):
        for layer in m.layer_set.all():
            layername = layer.layer.layername
            try:
                new_layer = server.layer_set.get(layername=layername)
            except Layer.DoesNotExist:
                continue
            layer.layer = new_layer
            layer.save(update_fields=('layer',))
            