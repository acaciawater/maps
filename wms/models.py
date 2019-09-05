from django.db import models
from django.utils.translation import gettext_lazy as _
from owslib.wms import WebMapService

WMS_VERSIONS=(
    ('1.1.1','1.1.1'),
    ('1.3.0','1.3.0'),
    )
class Server(models.Model):
    ''' WMS server '''
    name = models.CharField(_('name'), max_length=100, unique=True)
    url = models.URLField(_('url'), max_length=255)
    version = models.CharField(_('version'), max_length=10, default='1.3.0',choices=WMS_VERSIONS)
    
    def __str__(self):
        return self.name

    def service(self):
        return WebMapService(self.url, self.version)
    
    def layerDetails(self, layername = None):
        service = self.service()
        if layername is None:
            # return details of all layers
            return {layer: service[layer] for layer in service.contents}
        else:
            # single layer
            try:
                return {layername: service[layername]}
            except:
                return {}
    
    def enumLayers(self):
        for layer in self.service().contents:
            yield layer

    def updateLayers(self):

        # delete layers that are not reported in service contents
        newLayers = set(self.enumLayers())
        self.layer_set.exclude(layername__in=newLayers).delete()

        # create new layers if necessary
        numCreated = 0
        for layername, details in self.layerDetails().items():
            layer, created = self.layer_set.get_or_create(layername=layername,defaults = {
                'title': details.title or layername,
                'attribution': details.attribution.get('title','') if hasattr(details,'attribution') else ''})
            numCreated += 1
        return numCreated
                
    def getFeatureInfo(self,layers,xy,srs='EPSG:3857'):
        x,y = xy
        response = self.service().getfeatureinfo(
            layers=layers,
            srs=srs,
            bbox=(x-1,y-1,x+1,y+1),
            size=(3,3),
            format='image/jpeg',
            query_layers=layers,
            info_format="text/html",
            xy=(1,1))
        return response 
       
    class Meta:
        verbose_name = _('WMS-Server')
    
class Layer(models.Model):
    ''' Layer in a WMS server '''
    layername = models.CharField(_('layername'), max_length=100)
    title = models.CharField(_('title'), max_length=100)
    server = models.ForeignKey(Server,models.CASCADE,verbose_name=_('WMS Server'))
    tiled = models.BooleanField(_('tiled'), default=True)
    tiled.Boolean=True
    attribution = models.CharField(_('attribution'),max_length=200,blank=True,null=True,default='')
    bbox = models.CharField(_('extent'),max_length=100,null=True,blank=True)

    def __str__(self):
        return '{}:{}'.format(self.server, self.title or self.layername)

    def details(self):
        try:
            for _key, value in self.server.layerDetails(self.layername).items():
                return value
        except:
            return None
    
    def get_extent(self):
        details = self.details()
        return details.boundingBoxWGS84 if details else []
    
    def set_extent(self):
        ext = self.get_extent()
        self.bbox = ','.join(map(str,ext))
        self.save(update_fields=('bbox',))
        return ext
    
    def extent(self):
        if not self.bbox:
            return self.set_extent()
        else:
            return list(map(float,self.bbox.split(',')))
    
    def legend_url(self, style='default'):
        try:
            return self.details().styles[style]['legend']
        except:
            return None

class Meta:
        verbose_name = _('WMS-Layer')
    