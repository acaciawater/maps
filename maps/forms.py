'''
Created on Aug 29, 2019

@author: theo
'''
from django.forms.forms import Form
from django.forms import fields

class LayerPropertiesForm(Form):
    visible = fields.NullBooleanField(required=False)
    use_extent = fields.NullBooleanField(required=False)
    clickable = fields.NullBooleanField(required=False)
    transparent = fields.NullBooleanField(required=False)
    opacity = fields.DecimalField(max_digits=4, decimal_places=1,required=False)
    allow_download = fields.NullBooleanField(required=False)
    
