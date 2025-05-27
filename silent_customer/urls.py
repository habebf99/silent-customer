from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import requests
import os

def home(request):
    return HttpResponse("Welcome to Silent Customer!")

def install(request):
    client_id = os.environ.get('SALLA_CLIENT_ID')
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    auth_url = f'https://salla.sa/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=store.read+orders.read+offline_access'
    return HttpResponse(f'<a href="{auth_url}">Install App on Salla</a>')

def callback(request):
    code = request.GET.get('code')
    client_id = os.environ.get('SALLA_CLIENT_ID')
    client_secret = os.environ.get('SALLA_CLIENT_SECRET')
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    response = requests.post('https://accounts.salla.sa/oauth2/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    })
    return HttpResponse(response.json())

def webhook(request):
    if request.method == 'POST':
        return HttpResponse("Webhook received")
    return HttpResponse("Invalid request", status=400)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('install/', install),
    path('callback/', callback),
    path('webhook/', webhook),
]