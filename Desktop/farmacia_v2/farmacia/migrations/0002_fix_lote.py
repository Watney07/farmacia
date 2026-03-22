from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('farmacia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lote',
            name='cantidad_disponible',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Cantidad disponible'
            ),
        ),
    ]