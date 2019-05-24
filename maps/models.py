'''
Created on May 20, 2019

@author: theo
'''
from django.db import models
from django.utils.translation import gettext_lazy as _
from wms.models import Layer as WMSLayer
from django.utils.text import slugify
import json
from django.dispatch import receiver
from django.db.models.signals import pre_save
   
class Timeseries(models.Model):
    name = models.CharField(_('name'),max_length=100,unique=True)
    server = models.URLField(_('server'))
    locations = models.CharField(_('locations'),max_length=100)
    popup = models.CharField(_('popup'),max_length=100)
    chart = models.CharField(_('chart'),max_length=100)

    def __str__(self):
        return self.name
       
class Map(models.Model):
    name = models.CharField(_('name'),max_length=100,unique=True)

    def asjson(self):
        retval = {}
        for layer in self.layer_set.order_by('order'):
            retval[layer.layer.title]=layer.asjson()
        return json.dumps(retval)
    
    def __str__(self):
        return self.name
       
class Layer(models.Model): 
    map = models.ForeignKey(Map, models.CASCADE, verbose_name=_('map'))
    layer = models.ForeignKey(WMSLayer, models.CASCADE, verbose_name=_('WMS layer'),null=True)
    order = models.SmallIntegerField(_('order'))
    visible = models.BooleanField(_('visible'), default=True)    
    visible.boolean = True
    format = models.CharField(_('format'), max_length=50,default='image/png')
    minzoom = models.SmallIntegerField(_('maxzoom'),null=True, blank=True)
    maxzoom = models.SmallIntegerField(_('minzoom'),null=True, blank=True)
    transparent = models.BooleanField(_('transparent'), default=True)
    transparent.Boolean = True
    opacity = models.DecimalField(_('opacity'), max_digits=4, decimal_places=1, default=1.0)

    def asjson(self):
        ret = {
            'url': self.layer.server.url,
            'layers': self.layer.layername,
            'format': self.format,
            'visible': self.visible,
            'transparent': self.transparent,
            'opacity': float(self.opacity),
            }
        if self.minzoom:
            ret['minZoom'] = self.minzoom
        if self.maxzoom:
            ret['maxZoom'] = self.maxzoom
        try:
            ret['legend'] = self.layer.legend_url()
        except:
            ret['legend'] = ''
        return ret

    def __str__(self):
        return '{}'.format(self.layer)

class Project(models.Model):
    slug = models.SlugField(help_text=_('Short name for url'))
    name = models.CharField(_('name'),max_length=100,unique=True,help_text=_('Descriptive name of project'))
    title = models.CharField(_('tile'),max_length=100,help_text=_('Title on browser page'))
    logo = models.ImageField(_('logo'),upload_to='logos',null=True,blank=True)
    map = models.ForeignKey(Map,models.SET_NULL,null=True,blank=True,verbose_name=_('map'))
    timeseries = models.ForeignKey(Timeseries,models.SET_NULL,null=True,blank=True,verbose_name=_('timeseries'))
                                   
    def __str__(self):
        return self.name

@receiver(pre_save, sender=Project)
def project_save(sender, instance, **kwargs):
    if instance.slug is None:
        instance.slug = slugify(instance.name)
    
    