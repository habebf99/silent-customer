from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Silent Customer!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # رابط الصفحة الرئيسية
]