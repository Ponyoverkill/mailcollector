# Generated by Django 4.2.15 on 2024-08-31 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collector', '0003_alter_message_dispatch_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='text',
            field=models.TextField(blank=True, max_length=64535, null=True),
        ),
    ]
