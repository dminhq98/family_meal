# Generated by Django 3.2 on 2021-04-26 10:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ('-create_at',)},
        ),
    ]
