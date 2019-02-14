=====
CLICK
=====

Click is a simple Django application to working with click-api and conduct to Web-based.
Click module has integrated to "django-payments" module as variant.
You can find more information about "django-payments" by https://django-payments.readthedocs.io link.


Detailed documentation is in the https://docs.click.uz url.

Quick start
-----------
1. Installing
    $ pip install django-payments
    $ pip install click.tgz

2. Add "payments" and "click" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'payments',
        'click',
        ...
    ]

3. Add the variables to your settings.py like this::
    PAYMENT_HOST = '<your_ip_address>:<your_port>'
    PAYMENT_USES_SSL = False # set the True value if you are using the SSL
    PAYMENT_MODEL = '<your_payment_model>' # payment model format like this :: '<app_name>.<model_name>'
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

4. Include the click and payments URLconf in your project urls.py like this::

    path('payments/', include('payments.urls')),
    path('payments/', include('click.urls'))

5. Create your payment model to models.py like this::
    from payments.models import BasePayment
    class Payment(BasePayment):
        pass

6. Add the model to your admin.py like this::
    from django.contrib import admin

    # Register your models here.
    from .models import Payment

    class PaymentAdmin(admin.ModelAdmin):
        pass

    admin.site.register(Payment, PaymentAdmin)

7. Run `python manage.py migrate` to create the payment and your another models.

8. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a payment.

9. Click payment services:
    service urls as pattern : payments/process/click/service/<service_type>
    service types:
        1) create_invoice
        2) check_invoice
        3) create_card_token
        4) verify_card_token
        5) payment_with_token
        5) delete_card_token

10. The "prepare" and "complate" urls as pattern:
    prepare : payments/process/click/prepare
    complate : payments/process/click/complate

11. Example code at "example/" directory.