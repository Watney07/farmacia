"""
Script de datos de prueba — Sistema de Farmacia Grupo 6
========================================================
Ejecutar con: python manage.py shell < cargar_datos.py
"""
from farmacia.models import Medicamento, Lote
from decimal import Decimal
from datetime import date, timedelta

print("Cargando datos de prueba en PostgreSQL (Supabase)...")

# ── Medicamentos ──────────────────────────────────────────────────
medicamentos_data = [
    dict(nombre='Acetaminofén 500mg',    precio=Decimal('8500'),   requiere_receta=False,
         descripcion='Analgésico y antipirético de uso común.'),
    dict(nombre='Ibuprofeno 400mg',      precio=Decimal('12000'),  requiere_receta=False,
         descripcion='Antiinflamatorio no esteroideo.'),
    dict(nombre='Amoxicilina 500mg',     precio=Decimal('25000'),  requiere_receta=True,
         descripcion='Antibiótico de amplio espectro.'),
    dict(nombre='Loratadina 10mg',       precio=Decimal('9500'),   requiere_receta=False,
         descripcion='Antihistamínico para alergias.'),
    dict(nombre='Omeprazol 20mg',        precio=Decimal('15000'),  requiere_receta=False,
         descripcion='Inhibidor de la bomba de protones.'),
    dict(nombre='Metformina 850mg',      precio=Decimal('18000'),  requiere_receta=True,
         descripcion='Antidiabético oral de primera línea.'),
    dict(nombre='Atorvastatina 20mg',    precio=Decimal('22000'),  requiere_receta=True,
         descripcion='Reductor de colesterol.'),
    dict(nombre='Suero Oral Sobres',     precio=Decimal('4500'),   requiere_receta=False,
         descripcion='Sales de rehidratación oral.'),
]

medicamentos = {}
for m in medicamentos_data:
    obj, nuevo = Medicamento.objects.get_or_create(nombre=m['nombre'], defaults=m)
    medicamentos[m['nombre']] = obj
    estado = '✓ Creado' if nuevo else '→ Ya existía'
    print(f"  {estado}: {obj.nombre}")

# ── Lotes de inventario ───────────────────────────────────────────
hoy = date.today()

lotes_data = [
    # Lotes normales
    dict(medicamento=medicamentos['Acetaminofén 500mg'],
         numero_lote='ACE-2024-001', fecha_vencimiento=hoy + timedelta(days=365),
         cantidad_inicial=100, proveedor='Laboratorios MK'),
    dict(medicamento=medicamentos['Acetaminofén 500mg'],
         numero_lote='ACE-2024-002', fecha_vencimiento=hoy + timedelta(days=180),
         cantidad_inicial=50, proveedor='Laboratorios MK'),
    dict(medicamento=medicamentos['Ibuprofeno 400mg'],
         numero_lote='IBU-2024-001', fecha_vencimiento=hoy + timedelta(days=400),
         cantidad_inicial=80, proveedor='Genfar'),
    dict(medicamento=medicamentos['Amoxicilina 500mg'],
         numero_lote='AMO-2024-001', fecha_vencimiento=hoy + timedelta(days=300),
         cantidad_inicial=60, proveedor='GlaxoSmithKline'),
    dict(medicamento=medicamentos['Loratadina 10mg'],
         numero_lote='LOR-2024-001', fecha_vencimiento=hoy + timedelta(days=500),
         cantidad_inicial=120, proveedor='Tecnoquímicas'),
    dict(medicamento=medicamentos['Omeprazol 20mg'],
         numero_lote='OME-2024-001', fecha_vencimiento=hoy + timedelta(days=350),
         cantidad_inicial=90, proveedor='Pfizer'),
    # Lote con stock bajo (para probar alertas)
    dict(medicamento=medicamentos['Metformina 850mg'],
         numero_lote='MET-2024-001', fecha_vencimiento=hoy + timedelta(days=200),
         cantidad_inicial=5, proveedor='Sanofi'),
    # Lote próximo a vencer (para probar alerta de 30 días)
    dict(medicamento=medicamentos['Atorvastatina 20mg'],
         numero_lote='ATO-2024-001', fecha_vencimiento=hoy + timedelta(days=15),
         cantidad_inicial=30, proveedor='Novartis'),
    dict(medicamento=medicamentos['Suero Oral Sobres'],
         numero_lote='SUE-2024-001', fecha_vencimiento=hoy + timedelta(days=600),
         cantidad_inicial=200, proveedor='Abbott'),
]

creados = 0
for l in lotes_data:
    obj, nuevo = Lote.objects.get_or_create(
        numero_lote=l['numero_lote'],
        defaults={**l, 'cantidad_disponible': l['cantidad_inicial']}
    )
    if nuevo:
        creados += 1

print(f"\n  ✓ {creados} lotes creados")
print("\n⚠  Datos especiales para probar alertas:")
print("   - Metformina 850mg: stock bajo (5 unidades)")
print("   - Atorvastatina 20mg: lote vence en 15 días")
print("\n¡Listo! Prueba la API en: http://127.0.0.1:8000/api/")
print("Admin:                   http://127.0.0.1:8000/admin/")
print("Alertas:                 http://127.0.0.1:8000/api/medicamentos/alertas/")
