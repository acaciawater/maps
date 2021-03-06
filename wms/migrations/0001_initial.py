# Generated by Django 2.2.1 on 2019-05-21 08:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='name')),
                ('url', models.URLField(max_length=255, verbose_name='url')),
                ('version', models.CharField(choices=[('1.0.0', '1.0.0'), ('1.1.0', '1.1.0'), ('1.1.1', '1.1.1'), ('1.3.0', '1.3.0')], default='1.3.0', max_length=10, verbose_name='version')),
            ],
            options={
                'verbose_name': 'WMS-Server',
            },
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('layername', models.CharField(max_length=100, verbose_name='layername')),
                ('title', models.CharField(max_length=100, verbose_name='title')),
                ('tiled', models.BooleanField(default=True, verbose_name='tiled')),
                ('attribution', models.CharField(blank=True, default='', max_length=200, null=True, verbose_name='attribution')),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wms.Server', verbose_name='WMS Server')),
            ],
            options={
                'verbose_name': 'WMS-Layer',
            },
        ),
    ]
