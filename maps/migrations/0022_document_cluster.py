# Generated by Django 2.2.5 on 2020-03-30 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0021_auto_20200330_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='cluster',
            field=models.SmallIntegerField(default=0),
        ),
    ]