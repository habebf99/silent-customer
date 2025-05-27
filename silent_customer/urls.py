from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import requests
import os

def home(request):
    return HttpResponse("Welcome to Silent Customer!")

def install(request):
    # التحقق من المتغيرات عشان نتجنب client_id=None
    client_id = os.environ.get('SALLA_CLIENT_ID')
    if not client_id:
        return HttpResponse("Error: SALLA_CLIENT_ID is not set in environment variables", status=500)
    
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    auth_url = f'https://salla.sa/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=store.read+orders.read+offline_access'
    return HttpResponse(f'<a href="{auth_url}">Install App on Salla</a>')

def callback(request):
    code = request.GET.get('code')
    client_id = os.environ.get('SALLA_CLIENT_ID')
    client_secret = os.environ.get('SALLA_CLIENT_SECRET')
    
    # التحقق من المتغيرات
    if not client_id or not client_secret:
        return HttpResponse("Error: SALLA_CLIENT_ID or SALLA_CLIENT_SECRET is not set", status=500)
    
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    response = requests.post('https://accounts.salla.sa/oauth2/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    })
    
    # التحقق من الاستجابة
    if response.status_code != 200:
        return HttpResponse(f"Error: Failed to get token - {response.text}", status=response.status_code)
    
    return HttpResponse(response.json())

def webhook(request):
    # التحقق من Webhook Secret لزيادة الأمان
    webhook_secret = os.environ.get('SALLA_WEBHOOK_SECRET')
    if not webhook_secret:
        return HttpResponse("Error: SALLA_WEBHOOK_SECRET is not set", status=500)
    
    if request.method == 'POST':
        # هنا ممكن تضيف تحقق من التوقيع (Signature) لو سلة بتبعت واحد
        return HttpResponse("Webhook received")
    return HttpResponse("Invalid request", status=400)

# إضافة endpoint للتحقق من الإعدادات (Settings Validation)
def validate_settings(request):
    if request.method == 'POST':
        # هنا تضيف التحقق من البيانات اللي التاجر بيدخلها
        return HttpResponse("Settings validated", status=200)
    return HttpResponse("Invalid request", status=400)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('install/', install),
    path('callback/', callback),
    path('webhook/', webhook),
    path('settings/validate/', validate_settings),  # رابط التحقق من الإعدادات
]