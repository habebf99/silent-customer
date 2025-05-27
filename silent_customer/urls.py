from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import requests
import os
from .models import SallaToken # للتأكد من أن هذا السطر موجود إذا كنت تستورد SallaToken
from django.views.decorators.csrf import csrf_exempt # <-- هذا السطر مهم لإعفاء الـ webhook من حماية CSRF

def home(request):
    return HttpResponse("مرحبًا بك في عميلك الصامت!")

def install(request):
    client_id = os.environ.get('SALLA_CLIENT_ID')
    if not client_id:
        return HttpResponse("خطأ: SALLA_CLIENT_ID غير موجود", status=500)
    
    redirect_uri = 'https://silent-customer.onrender.com/callback' # أو الرابط المحلي إذا كنت تختبر محليًا وغيرت الإعدادات
    auth_url = f'https://salla.sa/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=store.read+orders.read+offline_access'
    return HttpResponse(f'<a href="{auth_url}">تثبيت التطبيق على سلة</a>')

def callback(request):
    code = request.GET.get('code')
    client_id = os.environ.get('SALLA_CLIENT_ID')
    client_secret = os.environ.get('SALLA_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return HttpResponse("خطأ: SALLA_CLIENT_ID أو SALLA_CLIENT_SECRET غير موجود", status=500)
    
    # يجب أن يكون هذا الـ redirect_uri مطابقًا تمامًا للـ redirect_uri الذي أرسلته في طلب authorize
    # وأحد الـ Callback URLs المسجلة في لوحة تحكم تطبيقك في سلة
    redirect_uri = 'https://silent-customer.onrender.com/callback' # أو المحلي إذا كنت تختبر محليًا

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
    
    # محاولة الحصول على معرّف التاجر (merchant ID) من الاستجابة أو من parameters الـ GET
    # قد يرسل سلة 'merchant' كـ subdomain أو كـ 'merchant_id' أو 'store_id'
    # تحتاج لمراجعة توثيق سلة أو تجربة لمعرفة الاسم الصحيح للمتغير
    store_id_from_salla = request.GET.get('merchant') or request.GET.get('merchant_id') or request.GET.get('store_id')
    
    # إذا لم يتم إرسال أي من هذه، يمكنك استخدام قيمة افتراضية أو محاولة استخراجه من مكان آخر
    store_id = store_id_from_salla if store_id_from_salla else "habeeb_default" # استخدمت قيمة افتراضية مختلفة قليلاً للتمييز

    # التأكد من أن النموذج SallaToken مستورد (from .models import SallaToken)
    # وأنك قمت بعمل makemigrations و migrate
    try:
        SallaToken.objects.update_or_create(
            store_id=store_id,
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': expires_in
            }
        )
        print(f"Token saved/updated for store_id: {store_id}")
    except Exception as e:
        print(f"Error saving token for store_id {store_id}: {e}")
        # يمكنك إرجاع خطأ هنا إذا فشل حفظ التوكن، أو التعامل معه بشكل مختلف
        return HttpResponse(f"خطأ في حفظ التوكن: {e}", status=500)
        
    return HttpResponse("تم تثبيت التطبيق بنجاح! 🎉 يمكنك الآن استخدام التطبيق مع متجرك.")

@csrf_exempt # <-- هذا السطر مهم جدًا هنا
def webhook(request):
    webhook_secret = os.environ.get('SALLA_WEBHOOK_SECRET')
    if not webhook_secret:
        print("SALLA_WEBHOOK_SECRET not configured on server.") # طباعة للمساعدة في التعقب على Render
        return HttpResponse("خطأ: SALLA_WEBHOOK_SECRET غير موجود في إعدادات الخادم", status=500)
    
    # TODO: أضف التحقق من توقيع الـ webhook هنا لاحقًا للأمان
    # salla_signature = request.headers.get('X-Salla-Signature')
    # if not verify_salla_signature(salla_signature, request.body, webhook_secret):
    #     return HttpResponse("توقيع غير صالح", status=403)

    if request.method == 'POST':
        print("Webhook received (POST):")
        try:
            # طباعة محتوى الـ webhook للمساعدة في الفهم والتعقب
            payload_str = request.body.decode('utf-8')
            print(f"Payload: {payload_str}")
            
            # هنا يمكنك إضافة كود لتحليل الـ JSON payload واستخدام البيانات
            # import json
            # data = json.loads(payload_str)
            # event_type = data.get('event')
            # print(f"Event type: {event_type}")
            # if event_type == 'app.installed':
            #     # قم بمعالجة حدث تثبيت التطبيق
            #     pass
            # elif event_type == 'order.created':
            #     # قم بمعالجة حدث إنشاء طلب جديد
            #     pass
            # ... وهكذا

        except Exception as e:
            print(f"Error processing webhook payload: {e}")
            # حتى لو حدث خطأ في المعالجة، من الأفضل إرجاع 200 لـ سلة لتجنب إعادة الإرسال المستمر
            # ولكن سجل الخطأ عندك للتحقيق
        
        return HttpResponse("تم استلام التنبيه بنجاح!", status=200)
    
    print(f"Webhook received with wrong method: {request.method}")
    return HttpResponse("طلب غير صالح (يجب أن يكون POST)", status=400)

def validate_settings(request):
    if request.method == 'POST':
        return HttpResponse("تم التحقق من الإعدادات", status=200)
    return HttpResponse("طلب غير صالح", status=400)

def get_store_info(request):
    # نفترض أننا سنبحث عن التوكن باستخدام store_id معين
    # في تطبيق حقيقي، قد يكون لديك طريقة لتحديد التاجر الحالي
    # أو قد ترغب في عرض معلومات لجميع المتاجر المثبت عليها التطبيق (إذا كان عامًا)
    # الآن، سنستخدم أول توكن موجود كالعادة للاختبار
    token_entry = SallaToken.objects.first() 
    if not token_entry:
        return HttpResponse("خطأ: لم يتم العثور على توكن. يرجى تثبيت التطبيق أولاً.", status=500)
    
    headers = {
        'Authorization': f'Bearer {token_entry.access_token}'
    }
    response = requests.get('https://api.salla.dev/api/v1/store', headers=headers)
    
    if response.status_code != 200:
        return HttpResponse(f"خطأ: فشل في جلب بيانات المتجر - {response.text}", status=response.status_code)
    
    store_data = response.json()
    store_name = store_data.get('data', {}).get('name', 'غير متوفر')
    return HttpResponse(f"اسم المتجر (من التوكن الخاص بـ {token_entry.store_id}): {store_name}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('install/', install),
    path('callback/', callback),
    path('webhook/', webhook),
    path('settings/validate/', validate_settings),
    path('store-info/', get_store_info),
]