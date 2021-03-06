# Generated by Django 2.2.1 on 2019-06-11 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0006_layer_use_extent'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='clickable',
            field=models.BooleanField(default=False, help_text='show popup with info when layer is clicked', verbose_name='clickable'),
        ),
        migrations.AddField(
            model_name='layer',
            name='properties',
            field=models.CharField(blank=True, help_text='comma separated list of properties to display when layer is clicked', max_length=200, null=True, verbose_name='properties'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='use_extent',
            field=models.BooleanField(default=True, verbose_name='Use extent'),
        ),
    ]
