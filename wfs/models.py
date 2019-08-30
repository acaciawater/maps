# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
from owslib.wfs import WebFeatureService

WFS_VERSIONS=(
    ('1.0.0','1.1.0'),
    ('2.0.0','3.0.0'),
    )
class Server(models.Model):
    ''' WFS server '''
    name = models.CharField(_('name'), max_length=100, unique=True)
    url = models.URLField(_('url'), max_length=255)
    version = models.CharField(_('version'), max_length=10, default='1.1.0',choices=WFS_VERSIONS)
    
    def __str__(self):
        return self.name

    def service(self):
        return WebFeatureService(self.url, self.version)
    
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
            if created:
                numCreated += 1
        return numCreated
                
    def getFeature(self,**kwargs):
        return self.service().getfeature(**kwargs)
       
    class Meta:
        verbose_name = _('WFS-Server')
    
class Layer(models.Model):
    ''' Layer in a WFS server '''
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
    