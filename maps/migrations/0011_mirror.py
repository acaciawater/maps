# Generated by Django 2.2.1 on 2019-08-28 13:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0002_auto_20190708_1448'),
        ('maps', '0010_auto_20190823_1519_squashed_0011_auto_20190823_1522'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mirror',
            fields=[
                ('map_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='maps.Map')),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wms.Server')),
            ],
            options={
                'abstract': False,
            },
            bases=('maps.map',),
        ),
    ]
