# Generated by Django 2.2.5 on 2019-10-30 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0015_auto_20190830_0831'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='layers',
            field=models.ManyToManyField(blank=True, to='maps.Layer'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='groups',
            field=models.ManyToManyField(blank=True, to='maps.Group', verbose_name='group'),
        ),
    ]
