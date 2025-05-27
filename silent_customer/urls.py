from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import json

def home(request):
    return HttpResponse("Welcome to Silent Customer!")

def webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get('event') == 'app.store.authorize':
            access_token = data.get('data', {}).get('access_token')
            refresh_token = data.get('data', {}).get('refresh_token')
            return HttpResponse(f"Access Token: {access_token}, Refresh Token: {refresh_token}")
        return HttpResponse("Webhook received")
    return HttpResponse("Invalid request", status=400)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('webhook/', webhook),
]