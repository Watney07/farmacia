from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Medicamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio unitario')),
                ('requiere_receta', models.BooleanField(default=False, verbose_name='Requiere receta')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Medicamento',
                'verbose_name_plural': 'Medicamentos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Lote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_lote', models.CharField(max_length=100, unique=True, verbose_name='Número de lote')),
                ('fecha_vencimiento', models.DateField(verbose_name='Fecha de vencimiento')),
                ('cantidad_inicial', models.PositiveIntegerField(verbose_name='Cantidad inicial')),
                ('cantidad_disponible', models.PositiveIntegerField(verbose_name='Cantidad disponible')),
                ('fecha_ingreso', models.DateField(auto_now_add=True)),
                ('proveedor', models.CharField(blank=True, max_length=200, verbose_name='Proveedor')),
                ('medicamento', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lotes',
                    to='farmacia.medicamento',
                    verbose_name='Medicamento',
                )),
            ],
            options={
                'verbose_name': 'Lote',
                'verbose_name_plural': 'Lotes',
                'ordering': ['fecha_vencimiento'],
            },
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(verbose_name='Cantidad')),
                ('precio_unitario_venta', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio unitario')),
                ('total', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12, verbose_name='Total')),
                ('cliente_nombre', models.CharField(blank=True, max_length=200, verbose_name='Cliente')),
                ('estado', models.CharField(
                    choices=[('completada', 'Completada'), ('cancelada', 'Cancelada')],
                    default='completada',
                    max_length=20,
                )),
                ('fecha_venta', models.DateTimeField(auto_now_add=True)),
                ('observaciones', models.TextField(blank=True)),
                ('medicamento', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='ventas',
                    to='farmacia.medicamento',
                    verbose_name='Medicamento',
                )),
                ('lote_usado', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='ventas',
                    to='farmacia.lote',
                    verbose_name='Lote usado',
                )),
            ],
            options={
                'verbose_name': 'Venta',
                'verbose_name_plural': 'Ventas',
                'ordering': ['-fecha_venta'],
            },
        ),
    ]
