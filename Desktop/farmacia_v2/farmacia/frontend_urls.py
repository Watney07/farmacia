from django.urls import path
from . import frontend_views

urlpatterns = [
    path('',               frontend_views.index,             name='index'),
    path('medicamentos/',  frontend_views.medicamentos_lista, name='medicamentos_lista'),
    path('ventas/',        frontend_views.ventas_lista,       name='ventas_lista'),
    path('alertas/',       frontend_views.alertas,            name='alertas'),
    path('login/',         frontend_views.login_view,         name='login_view'),
]
