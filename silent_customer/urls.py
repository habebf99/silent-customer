from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import requests
import os
from .models import SallaToken

def home(request):
    return HttpResponse("مرحبًا بك في عميلك الصامت!")

def install(request):
    client_id = os.environ.get('SALLA_CLIENT_ID')
    if not client_id:
        return HttpResponse("خطأ: SALLA_CLIENT_ID غير موجود", status=500)
    
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    auth_url = f'https://salla.sa/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=store.read+orders.read+offline_access'
    return HttpResponse(f'<a href="{auth_url}">تثبيت التطبيق على سلة</a>')

def callback(request):
    code = request.GET.get('code')
    client_id = os.environ.get('SALLA_CLIENT_ID')
    client_secret = os.environ.get('SALLA_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return HttpResponse("خطأ: SALLA_CLIENT_ID أو SALLA_CLIENT_SECRET غير موجود", status=500)
    
    redirect_uri = 'https://silent-customer.onrender.com/callback'
    response = requests.post('https://accounts.salla.sa/oauth2/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    })
    
    if response.status_code != 200:
        return HttpResponse(f"خطأ: فشل في الحصول على التوكن - {response.text}", status=response.status_code)
    
    token_data = response.json()
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in')
    
    # تخزين التوكن في قاعدة البيانات
    store_id = request.GET.get('merchant', 'habeeb')  # جيب store_id من الاستجابة
    SallaToken.objects.create(
        store_id=store_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )
    
    return HttpResponse("تم تثبيت التطبيق بنجاح! 🎉 يمكنك الآن استخدام التطبيق مع متجرك.")

def webhook(request):
    webhook_secret = os.environ.get('SALLA_WEBHOOK_SECRET')
    if not webhook_secret:
        return HttpResponse("خطأ: SALLA_WEBHOOK_SECRET غير موجود", status=500)
    
    if request.method == 'POST':
        return HttpResponse("تم استلام التنبيه")
    return HttpResponse("طلب غير صالح", status=400)

def validate_settings(request):
    if request.method == 'POST':
        return HttpResponse("تم التحقق من الإعدادات", status=200)
    return HttpResponse("طلب غير صالح", status=400)

def get_store_info(request):
    token = SallaToken.objects.first()
    if not token:
        return HttpResponse("خطأ: لم يتم العثور على توكن", status=500)
    
    headers = {
        'Authorization': f'Bearer {token.access_token}'
    }
    response = requests.get('https://api.salla.dev/api/v1/store', headers=headers)
    
    if response.status_code != 200:
        return HttpResponse(f"خطأ: فشل في جلب بيانات المتجر - {response.text}", status=response.status_code)
    
    store_data = response.json()
    store_name = store_data.get('data', {}).get('name', 'غير متوفر')
    return HttpResponse(f"اسم المتجر: {store_name}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('install/', install),
    path('callback/', callback),
    path('webhook/', webhook),
    path('settings/validate/', validate_settings),
    path('store-info/', get_store_info),
]