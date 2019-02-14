This module allows you to integrate payment acceptance using `"CLICK"` payment system into `Python Django` web applications.
Click-API module is integrated to `django-payments` module as payment provider.
Detailed documentation is available here __https://docs.click.uz__.

#### Installing
```
$ pip install django-payments
$ pip install click.tar.gz
```
#### Add `"payments"` and `"click"` to your `INSTALLED_APPS` setting like this::

```python
INSTALLED_APPS = [
    ...
    'payments',
    'click',
    ...
]
```
#### Add the variables to your `settings.py` like this::
```python
PAYMENT_HOST = '<your_ip_address>:<your_port>'
PAYMENT_USES_SSL = False # set the True value if you are using the SSL
PAYMENT_MODEL = '<your_payment_model>' 
# payment model format like this :: '<app_name>.<model_name>'
# add "click" to your variants
PAYMENT_VARIANTS = {
    ...
    'click' : ('click.ClickProvider', {
        'merchant_id' : 1111,
        'merchant_service_id' : 11111,
        'merchant_user_id' : 11111,
        'secret_key' : 'AAAAAA'
    })
    ...
}
```

#### Include the click and payments `URLconf` in your project `urls.py` like this::
```python
path('payments/', include('payments.urls'))
path('payments/', include('click.urls'))
```

#### Create your payment model to `models.py` like this::
```python
from payments.models import BasePayment
class Payment(BasePayment):
    pass
```

#### Add the model to your `admin.py` like this::
```python
from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    pass

admin.site.register(Payment, PaymentAdmin)
```
#### Run `python manage.py migrate` to create the payment and your other models.
#### Start the development server and visit `http://127.0.0.1:8000/admin/` to create a payment.
#### Click service urls as pattern : `payments/process/click/service/<service_type>` :
#### Service types
```
1) create_invoice
2) check_invoice
3) create_card_token
4) verify_card_token
5) payment_with_token
5) delete_card_token
```
#### The `"prepare"` and `"complete"` urls as pattern:
```
prepare : payments/process/click/prepare
complate : payments/process/click/complete
```
