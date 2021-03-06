'''
Created on May 20, 2019

@author: theo
'''
from django.db import models
from django.utils.translation import gettext_lazy as _
from wms.models import Layer as WMSLayer, Server
from django.utils.text import slugify
import json
from django.dispatch import receiver
from django.db.models.signals import pre_save
import collections
from django.urls.base import reverse

class MapsModel(models.Model):
    '''
    Abstract base model that adds 'app_label' and 'model_name' properties to model for use with admin:admin_urls template tag
    '''
    @property
    def app_label(self):
        return self._meta.app_label

    @property
    def model_name(self):
        return self._meta.model_name

    class Meta:
        abstract = True
        app_label = 'maps'
        
class Timeseries(MapsModel):
    name = models.CharField(_('name'),max_length=100,unique=True)
    server = models.URLField(_('server'))
    locations = models.CharField(_('locations'),max_length=100)
    popup = models.CharField(_('popup'),max_length=100)
    chart = models.CharField(_('chart'),max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Timeseries'
        
class Map(MapsModel):
    
    name = models.CharField(_('name'),max_length=100,unique=True)
    bbox = models.CharField(_('extent'),max_length=100,null=True,blank=True)

    def layers(self):
        retval = collections.OrderedDict()
        for layer in self.layer_set.order_by('order'):
            retval[layer.layer.title]=layer.asjson()
        return json.dumps(retval)

    def groups(self):
        groups = {}

        ungrouped = self.layer_set.filter(groups__isnull=True).order_by('order').prefetch_related('groups')
        if ungrouped:
            groups['Layers'] = collections.OrderedDict()
            for layer in ungrouped:
                groups['Layers'][layer.layer.title]=layer.asjson()
            
        for group in self.group_set.order_by('name').prefetch_related('layers'):
            groups[group.name] = collections.OrderedDict()
            for layer in group.layers.order_by('order'):
                groups[group.name][layer.layer.title]=layer.asjson()

        return json.dumps(groups)
                
            
    def get_extent(self):
        map_extent = []
        for layer in self.layer_set.exclude(use_extent=False):
            bbox = layer.extent()
            if bbox:
                if map_extent:
                    map_extent[0] = min(bbox[0], map_extent[0])
                    map_extent[1] = min(bbox[1], map_extent[1])
                    map_extent[2] = max(bbox[2], map_extent[2])
                    map_extent[3] = max(bbox[3], map_extent[3])
                else:
                    map_extent = list(bbox)
        return map_extent
    
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
      
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('map-detail', args=[self.pk])        

class Mirror(Map):

    server = models.ForeignKey(Server,on_delete=models.CASCADE)
    
    def update_layers(self):
        # update layer list on WMS server
        self.server.updateLayers()
        
        # update layer list of this map
        self.layer_set.all().delete()
        index = 0
        for layer in self.server.layer_set.all():
            self.layer_set.create(layer=layer,order=index,use_extent=False)
            index += 1
        return index

class Group(models.Model):
    name = models.CharField(_('group'), max_length=100)
    map = models.ForeignKey(Map,on_delete=models.CASCADE)
    layers = models.ManyToManyField('maps.Layer',blank=True)

    def layer_count(self):
        return self.layers.count()
        
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        unique_together = ('name','map')
        
class Layer(MapsModel): 
    map = models.ForeignKey(Map, models.CASCADE, verbose_name=_('map'))
    layer = models.ForeignKey(WMSLayer, models.CASCADE, verbose_name=_('WMS layer'),null=True)
    groups = models.ManyToManyField(Group, blank=True, verbose_name=_('group'), through='maps.group_layers')
    order = models.SmallIntegerField(_('order'))
    visible = models.BooleanField(_('visible'), default=True)    
    visible.boolean = True
    format = models.CharField(_('format'), max_length=50,default='image/png')
    minzoom = models.SmallIntegerField(_('minzoom'),null=True, blank=True)
    maxzoom = models.SmallIntegerField(_('maxzoom'),null=True, blank=True)
    transparent = models.BooleanField(_('transparent'), default=True)
    transparent.Boolean = True
    opacity = models.DecimalField(_('opacity'), max_digits=4, decimal_places=1, default=1.0)

    use_extent = models.BooleanField(default=True,verbose_name=_('Use extent'))
    clickable = models.BooleanField(default=False,verbose_name=_('clickable'),help_text=_('show popup with info when layer is clicked'))
    clickable.boolean = True
    properties = models.CharField(_('properties'), max_length=200, null=True, blank=True, help_text=_('comma separated list of properties to display when layer is clicked')) 

    allow_download = models.BooleanField(default=False,verbose_name=_('downloadable'), help_text=_('user can download this layer'))
    allow_download.Boolean=True
    download_url = models.URLField(_('download url'),null=True,blank=True,help_text=_('url for download of entire layer'))
    stylesheet = models.URLField(_('stylesheet'),null=True, blank=True, help_text=_('url of stylesheet for GetFeatureInfo response'))

    def group_names(self):
        return ','.join(map(str,self.groups.values_list('name',flat=True)))

    def extent(self):
        return self.layer.extent()
    
    def asjson(self):
        '''
        returns json dict for L.tileLayer.wms
        '''
        ret = {
            'url': self.layer.server.url,
            'layers': self.layer.layername,
            'format': self.format,
            'visible': self.visible,
            'transparent': self.transparent,
            'opacity': float(self.opacity),
            'clickable': self.clickable,
            'displayName': self.layer.title,
            }
        if self.properties:
            ret['propertyName'] = self.properties
        if self.allow_download and self.download_url:
            ret['downloadUrl'] = self.download_url
        if self.stylesheet:
            ret['stylesheet'] = self.stylesheet
        if self.minzoom:
            ret['minZoom'] = self.minzoom
        if self.maxzoom:
            ret['maxZoom'] = self.maxzoom
        try:
            ret['legend'] = self.layer.legend_url()
        except:
            pass #ret['legend'] = ''
        return ret

    def __str__(self):
        return '{}'.format(self.layer)

class Project(MapsModel):
    slug = models.SlugField(help_text=_('Short name for url'))
    name = models.CharField(_('name'),max_length=100,unique=True,help_text=_('Descriptive name of project'))
    title = models.CharField(_('tile'),max_length=100,help_text=_('Title on browser page'))
    logo = models.ImageField(_('logo'),upload_to='logos',null=True,blank=True)
    map = models.ForeignKey(Map,models.SET_NULL,null=True,blank=True,verbose_name=_('map'))
    timeseries = models.ForeignKey(Timeseries,models.SET_NULL,null=True,blank=True,verbose_name=_('timeseries'))
                      
    def get_absolute_url(self):
        return reverse('project-detail', args=[self.pk])        

    def __str__(self):
        return self.name
    
@receiver(pre_save, sender=Project)
def project_save(sender, instance, **kwargs):
    if instance.slug is None:
        instance.slug = slugify(instance.name)
    