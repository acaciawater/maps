from django.db import models
from django.utils.translation import gettext_lazy as _

class WMSServer(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    url = models.URLField(_('url'), max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('WMS-Server')
    
class WMSLayer(models.Model):
    layername = models.CharField(_('layername'), max_length=100)
    server = models.ForeignKey(WMSServer,models.CASCADE,verbose_name=_('WMS Server'))

    def __str__(self):
        return '{}:{}'.format(self.server, self.layername)

    class Meta:
        verbose_name = _('WMS-Layer')
    
class Layer(models.Model):
    name = models.CharField(_('name'),max_length=100)
    #layer = models.ForeignKey(WMSLayer, models.CASCADE, verbose_name=_('WMS layer'))
    source = models.ForeignKey(WMSLayer, models.CASCADE, verbose_name=_('WMS layer'),null=True,related_name='aap')
    minzoom = models.SmallIntegerField(_('maxzoom'),null=True, blank=True)
    maxzoom = models.SmallIntegerField(_('minzoom'),null=True, blank=True)
    opacity = models.DecimalField(_('opacity'), max_digits=4, decimal_places=1, default=1.0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Layer configuration')

class Map(models.Model):
    name = models.CharField(_('name'), max_length=100, unique = True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Map')

class MapLayer(models.Model):
    map = models.ForeignKey(Map, models.CASCADE, verbose_name=_('map'), related_name='layers')
    layer = models.ForeignKey(Layer, models.CASCADE, verbose_name=_('layer'))
    order = models.SmallIntegerField(_('order'))
    visible = models.BooleanField(_('visible'), default=True)    
    visible.boolean = True
    
    def __str__(self):
        return '{}:{}'.format(self.map.name, self.layer.name)
