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
            return {layername: service[layername]}
    
    def enumLayers(self):
        for layer in self.service().contents:
            yield layer
            
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

    def __str__(self):
        return '{}:{}'.format(self.server, self.title or self.layername)

    def details(self):
        for _key, value in self.server.layerDetails(self.layername).items():
            return value
    
    def extent(self):
        details = self.details()
        return details.boundingBoxWGS84
    
    def legend_url(self, style='default'):
        return self.details().styles[style]['legend']

    class Meta:
        verbose_name = _('WMS-Layer')
    