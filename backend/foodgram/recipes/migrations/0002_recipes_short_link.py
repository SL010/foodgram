# Generated by Django 3.2.4 on 2024-09-06 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipes',
            name='short_link',
            field=models.URLField(blank=True, verbose_name='Сокращенная ссылка'),
        ),
    ]
