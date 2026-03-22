from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def medicamentos_lista(request):
    return render(request, 'medicamentos.html')


def ventas_lista(request):
    return render(request, 'ventas.html')


def alertas(request):
    return render(request, 'alertas.html')


def login_view(request):
    return render(request, 'login.html')
