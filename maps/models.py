'''
Created on May 20, 2019

@author: theo
'''
import collections
import json

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls.base import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from sorl.thumbnail import ImageField
from wms.models import Layer as WMSLayer
from wms.models import Server


class MapsModel(models.Model):
    '''
    Abstract base model that adds 'app_label' and 'model_name' properties to model
    for use with admin:admin_urls template tag
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
    ''' model that links with timeseries from a remote meetnet app '''
    name = models.CharField(_('name'), max_length=100, unique=True)
    server = models.URLField(_('server'))
    locations = models.CharField(_('locations'), max_length=100)
    popup = models.CharField(_('popup'), max_length=100)
    chart = models.CharField(_('chart'), max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Timeseries'


class Map(MapsModel):
    ''' Collection of map layers '''
    slug = models.SlugField(help_text=_('Short name for map'), null=True)
    name = models.CharField(_('name'), max_length=100, unique=True)
    bbox = models.CharField(_('extent'), max_length=100, null=True, blank=True)

    def layers(self):
        ''' return ordered json dictionary of all layers using wms title as key '''
        retval = collections.OrderedDict()
        for layer in self.layer_set.order_by('order'):
            retval[layer.layer.title] = layer.wms_options()
        return json.dumps(retval)

    def groups(self):
        ''' return json dictionary of groups with group name as key
        and ordered dictionary of layers as values '''
        groups = {}

        # Add ungrouped layers with default group name 'Layers'
        ungrouped = self.layer_set.filter(group__isnull=True).order_by('order')
        if ungrouped:
            groups['Layers'] = collections.OrderedDict()
            for layer in ungrouped:
                groups['Layers'][layer.layer.title] = layer.wms_options()

        # add all groups and layers
        for group in self.group_set.order_by('name'):
            groups[group.name] = collections.OrderedDict()
            for layer in group.layer_set.order_by('order'):
                groups[group.name][layer.layer.title] = layer.wms_options()

        return json.dumps(groups)

    def get_extent(self):
        ''' compute and return map extent from layers '''
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
        ''' update self.bbox with string representation of current extent '''
        ext = self.get_extent()
        self.bbox = ','.join(map(str, ext))
        self.save(update_fields=('bbox',))
        return ext

    def extent(self):
        ''' return current extent. Calculate if self.bbox is undefined '''
        return list(map(float, self.bbox.split(','))) if self.bbox else self.set_extent()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('map-detail', args=[self.pk])


@receiver(pre_save, sender=Map)
def map_save(sender, **kwargs):
    instance = sender
    if instance.slug is None:
        instance.slug = slugify(instance.name)


class Mirror(Map):
    ''' A map that mirrors all layers on a WMS server '''
    server = models.ForeignKey(Server, on_delete=models.CASCADE)

    def update_layers(self):
        # update layer list on WMS server
        self.server.updateLayers()

        # update layer list of this map
        self.layer_set.all().delete()
        index = 0
        for layer in self.server.layer_set.all():
            self.layer_set.create(layer=layer, order=index, use_extent=False)
            index += 1
        return index


class Group(models.Model):
    ''' Layer group '''
    name = models.CharField(_('group'), max_length=100)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)

    def layer_count(self):
        return self.layer_set.count()

    def __str__(self):
        return '{}:{}'.format(self.map.name, self.name)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        unique_together = ('name', 'map')


class Layer(MapsModel):
    '''
    Layer on the map.
    Layer can be configured (by order, visibility, opacity etc)
    Currently only WMS layers are supported
    '''
    map = models.ForeignKey(Map, models.CASCADE, verbose_name=_('map'))
    layer = models.ForeignKey(WMSLayer, models.CASCADE,
                              verbose_name=_('WMS layer'), null=True)
    group = models.ForeignKey(Group, models.SET_NULL,
                              blank=True, null=True, verbose_name=_('group'))
    order = models.SmallIntegerField(_('order'))
    visible = models.BooleanField(_('visible'), default=True)
    visible.boolean = True
    format = models.CharField(_('format'), max_length=50, default='image/png')
    minzoom = models.SmallIntegerField(_('minzoom'), null=True, blank=True)
    maxzoom = models.SmallIntegerField(_('maxzoom'), null=True, blank=True)
    transparent = models.BooleanField(_('transparent'), default=True)
    transparent.Boolean = True
    opacity = models.DecimalField(
        _('opacity'), max_digits=4, decimal_places=1, default=1.0)

    use_extent = models.BooleanField(
        default=True, verbose_name=_('Use extent'))
    clickable = models.BooleanField(default=False, verbose_name=_(
        'clickable'), help_text=_('show popup with info when layer is clicked'))
    clickable.boolean = True
    properties = models.CharField(_('properties'), max_length=200, null=True, blank=True,
                                  help_text=_(
                                      'comma separated list of properties to display when layer is clicked'))

    allow_download = models.BooleanField(default=False, verbose_name=_(
        'downloadable'), help_text=_('user can download this layer'))
    allow_download.Boolean = True
    download_url = models.URLField(_('download url'), null=True, blank=True, help_text=_(
        'url for download of entire layer'))
    stylesheet = models.URLField(_('stylesheet'), null=True, blank=True, help_text=_(
        'url of stylesheet for GetFeatureInfo response'))

    def extent(self):
        ''' return extent of WMS layer in WGS84 coordinates '''
        return self.layer.extent()

    def wms_options(self):
        '''
        returns options dict for L.tileLayer.wms
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
            # logger.error('Failed to retrieve legend url')
            pass  # ret['legend'] = ''
        return ret

    def __str__(self):
        return '{}'.format(self.layer)


class UserConfig(models.Model):
    ''' User config (layer visibility and order) '''
    user = models.ForeignKey(User, models.CASCADE, verbose_name=_('user'))
    layer = models.ForeignKey(Layer, models.CASCADE, verbose_name=_('layer'))
    order = models.SmallIntegerField(_('order'), default=0)
    visible = models.BooleanField(default=True)

    @classmethod
    def sync(cls, user, map_instance):
        ''' Synchronize user configuration with default map layers '''
        layers = map_instance.layer_set.all()
        # Delete configuration for layers that are not on the map anymore
        cls.objects.filter(user=user, layer__map=map_instance).exclude(
            layer__in=layers).delete()
        # create missing config of map layers for this user
        numcreated = 0
        for layer in map_instance.layer_set.all():
            _, created = cls.objects.get_or_create(user=user, layer=layer, defaults={
                'order': layer.order, 'visible': layer.visible
            })
            if created:
                numcreated += 1
        return numcreated

    @classmethod
    def update(cls, user, map_instance):
        ''' Update user configuration from default map layers. (This is a reset to default) '''
        layers = map_instance.layer_set.all()
        # Delete configuration for layers that are not on the map anymore
        cls.objects.filter(user=user, layer__map=map_instance).exclude(
            layer__in=layers).delete()
        # create missing config of map layers for this user
        numcreated = 0
        for layer in map_instance.layer_set.all():
            _, created = cls.objects.update_or_create(user=user, layer=layer, defaults={
                'order': layer.order, 'visible': layer.visible
            })
            if created:
                numcreated += 1
        return numcreated

    @classmethod
    def groups(cls, user, map_instance):
        ''' return json dict of groups with layers on the map. Layers are ordered by user's preference '''

        groups = {}

        def add(layer):
            name = layer.group.name if layer.group else 'Layers'
            if name not in groups:
                groups[name] = collections.OrderedDict()
            groups[name][layer.layer.title] = layer.wms_options()

        for config in cls.objects.filter(user=user, layer__map=map_instance).order_by('order'):
            layer = config.layer
            # set visibility and order according to user's preference
            layer.order = config.order
            layer.visible = config.visible
            add(layer)
        return json.dumps(groups)

    def __str__(self):
        return '{}:{}'.format(self.layer.map, self.layer.layer.title)

    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'


class Project(MapsModel):
    slug = models.SlugField(help_text=_('Short name for url'))
    name = models.CharField(_('name'), max_length=100, unique=True, help_text=_(
        'Descriptive name of project'))
    title = models.CharField(_('tile'), max_length=100,
                             help_text=_('Title on browser page'))
    logo = models.ImageField(
        _('logo'), upload_to='logos', null=True, blank=True)
    map = models.ForeignKey(Map, models.SET_NULL, null=True,
                            blank=True, verbose_name=_('map'))
    timeseries = models.ForeignKey(
        Timeseries, models.SET_NULL, null=True, blank=True, verbose_name=_('timeseries'))

    def get_absolute_url(self):
        return reverse('project-detail', args=[self.pk])

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Project)
def project_save(_sender, instance, **_kwargs):
    if instance.slug is None:
        instance.slug = slugify(instance.name)


class DocumentGroup(models.Model):
    name = models.CharField(max_length=100)    
    parent = models.ForeignKey('DocumentGroup', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    
    def docs(self,cluster=0):
        ''' returns complete list of documents of this group and its children '''
        query = self.document_set.all()
        if cluster:
            query = query.filter(cluster=cluster)  
        for doc in query:
            yield doc
        for child in self.children.all():
            yield from child.docs(cluster)
        
    def empty(self,cluster=0):
        ''' returns true if there are no documents in this group, or any of its children ''' 
        try:
            next(self.docs(cluster))
            return False
        except StopIteration:
            return True
    
    def __str__(self):
        if self.parent and self.parent.parent is not None:
            # insert parent name, except when parent is root
            return f'{self.parent}-{self.name}'
        else:
            return self.name


def upload_to_cluster(instance, filename):
    return 'cluster{0}/{1}'.format(instance.cluster or 0, filename)
    
class Document(models.Model):
    ''' Downloadable document '''
    group = models.ForeignKey(DocumentGroup,on_delete=models.CASCADE)
    cluster = models.CharField(max_length=30,blank=True,null=True)
    name = models.CharField(max_length=100)    
    description = models.TextField(blank=True, null=True)
    url = models.URLField()
    doc = ImageField(upload_to=upload_to_cluster, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)
    