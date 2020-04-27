# Generated by Django 2.1.7 on 2019-04-03 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0050_customimagewithauthor_customrenditionwithauthor'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimpleProxyPage',
            fields=[
            ],
            options={
                'indexes': [],
                'proxy': True,
            },
            bases=('tests.simplepage',),
        ),
        migrations.CreateModel(
            name='ProxyAdvert',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('tests.advert',),
        ),
        migrations.CreateModel(
            name='SimpleProxyPageDeux',
            fields=[
            ],
            options={
                'indexes': [],
                'proxy': True,
            },
            bases=('tests.simplepage',),
        ),
    ]
