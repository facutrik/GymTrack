from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('asistencias', '0001_initial'),
        ('socios', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='asistencia',
            name='socio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socios.socio'),
        ),
    ]
