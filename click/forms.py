from __future__ import unicode_literals

from requests.exceptions import HTTPError

from django.utils.translation import ugettext_lazy as _
from django import forms
from payments.forms import CreditCardPaymentFormWithName, PaymentForm
from payments.fields import CreditCardNumberField
from payments.core import get_credit_card_issuer
from payments import PaymentStatus

from time import strftime
import hashlib, json

class PaymentButtonForm(PaymentForm):
    def __init__(self, provider = None, payment = None):
        self.sign_time = strftime('%Y-%m-%d')
        self.provider = provider
        self.payment = payment

        self.hidden_inputs = {
            'MERCHANT_TRANS_AMOUNT' : self.payment.total,
            'MERCHANT_ID' : self.provider.merchant_id,
            'MERCHANT_USER_ID' : self.provider.merchant_user_id,
            'MERCHANT_SERVICE_ID' : self.provider.merchant_service_id,
            'MERCHANT_TRANS_ID' : self.payment.transaction_id,
            'MERCHANT_TRANS_NOTE' : self.payment.description,
            'MERCHANT_USER_EMAIL' : self.payment.billing_email,
            'SIGN_TIME' : self.sign_time,
            'SIGN_STRING' : self.sign_string(),
            'RETURN_URL' : self.return_url()
        }
        super(PaymentButtonForm, self).__init__(
            action = 'https://my.click.uz/pay/',
            provider = provider,
            payment = payment
        )
        for key, val in self.hidden_inputs.items():
            widget = forms.widgets.HiddenInput()
            self.fields[key] = forms.CharField(initial=val, widget=widget)


    def return_url(self):
        try:
            extra_data = json.loads(self.payment.extra_data)
            links = extra_data.get("links", {})
            if "return" in links:
                return links["return"]
        except Exception as e:
            pass
        return "/"

    
    def sign_string(self):
        encoder = hashlib.md5()
        string = '{sign_time}{secret_key}{merchant_service_id}{merchant_trans_id}{amount}'.format(
            sign_time = self.sign_time,
            secret_key = self.provider.secret_key,
            merchant_service_id = self.provider.merchant_service_id,
            merchant_trans_id = self.payment.transaction_id,
            amount = self.payment.total
        )
        encoder.update(string.encode('utf-8'))
        return encoder.hexdigest()

class PaymentPhoneNumberForm(PaymentForm):
    def __init__(self, provider = None, payment = None):
        super(PaymentPhoneNumberForm, self).__init__(
            action = '/payments/process/click/{payment_id}/create'.format(payment_id = payment.id),
            provider = provider,
            payment = payment
        )
        self.provider = provider
        self.payment = payment
        self.fields['phone_number'] = forms.CharField(
            widget = forms.TextInput(attrs = {'class':'form-control', 'placeholder' : '998MMNNNNNNN'})
        )

class PaymentCardNumberForm(PaymentForm):
    def __init__(self, provider = None, payment = None):
        super(PaymentCardNumberForm, self).__init__(
            action = '/payments/process/click/{payment_id}/create'.format(payment_id = payment.id),
            provider = provider,
            payment = payment
        )
        self.provider = provider
        self.payment = payment
        self.fields['card_number'] = forms.CharField(
            max_length = 16,
            widget = forms.TextInput(attrs = {'class':'form-control', 'placeholder' : '8600AAAABBBBCCCCDDDD'})
        )
        self.fields['expire_date'] = forms.CharField(
            max_length = 4,
            widget = forms.TextInput(attrs = {'class':'form-control', 'placeholder' : 'MMYY'})
        )
        self.fields['temporary']  = forms.ChoiceField(
            choices = (
                (0, 'NO'),
                (1, 'YES')
            ),
            widget = forms.Select(attrs = {'class' : 'form-control'})
        )
        self.fields['sms_code'] = forms.CharField(
            max_length = 5,
            widget = forms.widgets.TextInput(attrs = {'class':'form-control'}),
            required = None
        )