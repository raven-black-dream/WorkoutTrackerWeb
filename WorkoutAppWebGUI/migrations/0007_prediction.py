# Generated by Django 3.1.2 on 2021-08-12 23:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('WorkoutAppWebGUI', '0006_auto_20210701_1921'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avg_reps', models.DecimalField(decimal_places=5, max_digits=8)),
                ('avg_rpe', models.DecimalField(decimal_places=5, max_digits=7)),
                ('recommendation', models.IntegerField()),
                ('user_agrees', models.BooleanField()),
                ('user_suggestion', models.IntegerField()),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='WorkoutAppWebGUI.exercisetype')),
                ('workout_id', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='WorkoutAppWebGUI.workout')),
            ],
        ),
    ]