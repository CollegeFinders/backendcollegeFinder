# Generated by Django 5.1.2 on 2025-01-02 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_college_image_alter_college_logo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='college',
            name='image',
            field=models.FileField(upload_to='images'),
        ),
        migrations.AlterField(
            model_name='college',
            name='logo',
            field=models.FileField(upload_to='logos'),
        ),
    ]
