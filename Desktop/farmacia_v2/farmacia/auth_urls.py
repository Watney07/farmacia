from django.urls import path
from .views import LoginView, LogoutView, PerfilView

urlpatterns = [
    path('login/',    LoginView.as_view(),    name='login'),
    path('logout/',   LogoutView.as_view(),   name='logout'),
    path('perfil/',   PerfilView.as_view(),   name='perfil'),
]
