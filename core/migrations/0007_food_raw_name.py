# Generated by Django 2.1.7 on 2019-04-26 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("core", "0006_auto_20190421_1833")]

    operations = [
        migrations.AddField(
            model_name="food",
            name="raw_name",
            field=models.CharField(default="abc", max_length=100),
            preserve_default=False,
        )
    ]
