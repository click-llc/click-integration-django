from decimal import Decimal 
import time
import logging

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils import timezone
import requests, json, hashlib
from requests.exceptions import HTTPError

from .forms import PaymentButtonForm, PaymentPhoneNumberForm, PaymentCardNumberForm
from payments import PaymentError, PaymentStatus, RedirectNeeded, get_payment_model
from payments.core import BasicProvider
from payments.core import provider_factory
from django.shortcuts import get_object_or_404

# Get an instance of a logger
logger = logging.getLogger(__name__)

CENTS = Decimal('0.01')

class ApiHelper:
    endpoint = 'https://api.click.uz/v1/merchant'

    def __init__(self, provider, payment, data, **kwargs):
        self.provider = provider
        self.payment = payment
        self.data = data
        self.timestaps = int(time.time())
        self.token = hashlib.sha1('{timestaps}{secret_key}'.format(
                timestaps = self.timestaps, secret_key = self.provider.secret_key
            ).encode('utf-8')
        ).hexdigest()
    
    def get_extra_data(self):
        extra_data = {}
        try:
            extra_data = json.loads(self.payment.extra_data)
        except Exception as e:
            pass
        return extra_data
    
    def save_extra_data(self, extra_data):
        self.payment.extra_data = json.dumps(extra_data)
        self.payment.save()

    def post(self, url, data):
        response = requests.post(self.endpoint + url, json = data, headers = {
            'Content-Type' : 'application/json',
            'Accept' : 'application/json',
            'Auth' : '{}:{}:{}'.format(self.provider.merchant_user_id, self.token, self.timestaps)
        })
        return response
    
    def get(self, url):
        response = requests.get(self.endpoint + url, headers = {
            'Content-Type' : 'application/json',
            'Accept' : 'application/json',
            'Auth' : '{}:{}:{}'.format(self.provider.merchant_user_id, self.token, self.timestaps)
        })
        return response

    def check_invoice(self):
        self.invoice_id = self.data['invoice_id']
        check_invoice = self.get('/invoice/status/{service_id}/{invoice_id}'.format(
            service_id = self.provider.merchant_service_id,
            invoice_id = self.invoice_id
        ))
        if check_invoice.status_code == 200:
            _json = check_invoice.json()
            if _json['status'] > 0:
                self.payment.change_status(PaymentStatus.CONFIRMED)
            elif _json['status'] == -99:
                self.payment.change_status(PaymentStatus.REJECTED)
            elif _json['status'] < 0:
                self.payment.change_status(PaymentStatus.ERROR)
            self.payment.message = json.dumps(_json)
            self.payment.save()
            return _json
        else:
            return {
                'error' : -1 * check_invoice.status_code,
                'error_note' : 'Http request error [{}]'.format(check_invoice.status_code),
                'status' : -1 * check_invoice.status_code,
                'staus_note' : 'Http request error [{}]'.format(check_invoice.status_code)
            }

    def create_invoice(self):
        if self.payment.status == PaymentStatus.INPUT:
            invoice = self.post('/invoice/create', {
                'service_id' : self.provider.merchant_service_id,
                'amount' : float(self.payment.total),
                'phone_number' : self.data['phone_number'],
                'merchant_trans_id' : self.payment.transactions_id
            })
            if invoice.status_code == 200:
                _json = invoice.json()
                extra_data = self.get_extra_data()
                extra_data['payment'] = {
                    'type' : 'phone_number',
                    'phone_number' : self.data['phone_number'],
                    'invoice' : _json
                }
                self.save_extra_data(extra_data)
                if _json['error_code'] == 0:
                    self.payment.change_status(PaymentStatus.WAITING)
                else:
                    self.payment.change_status(PaymentStatus.ERROR)
                self.payment.message = json.dumps(_json)
                self.payment.save()
                return _json
            else:
                return {
                    'error' : -1 * invoice.status_code,
                    'error_note' : 'Http request error [{}]'.format(invoice.status_code)
                }
        else:
            return {
                'error' : -5001,
                'error_note' : 'Payment could not found'
            }

    def create_card_token(self):
        if self.payment.status == PaymentStatus.INPUT:
            data = {
                'service_id' : self.provider.merchant_service_id,
                'card_number' : self.data['card_number'],
                'expire_date' : self.data['expire_date'],
                'temporary' : self.data['temporary']
            }
            response = self.post('/card_token/request', data = data)
            if response.status_code == 200:
                _json = response.json()

                extra_data = self.get_extra_data()
                extra_data['payment'] = {
                    'type' : 'card_number',
                    'card_number' : self.data['card_number'],
                    'temporary' : self.data['temporary'],
                    'card_token' : _json
                }
                if _json['error_code'] == 0:
                    self.payment.change_status(PaymentStatus.WAITING)
                else:
                    self.payment.change_status(PaymentStatus.ERROR)
                self.payment.message = json.dumps(_json)
                self.payment.save()
                return _json
            return {
                'error' : -1 * response.status_code,
                'error_note' : 'Http request error [{}]'.format(response.status_code)
            }
        else:
            return {
                'error' : 5001,
                'error_note' : 'Payment could not found'
            }
    
    def verify_card_token(self):
        if self.payment.status != PaymentStatus.CONFIRMED:
            data = {
                'service_id' : self.provider.merchant_service_id,
                'card_token' : self.data['card_token'],
                'sms_code' : self.data['sms_code']
            }
            response = self.post('/card_token/payment', data)
            if response.status_code == 200:
                _json = response.json()
                if _json['error_code'] == 0:
                    self.payment.change_status(PaymentStatus.CONFIRMED)
                else:
                    self.payment.change_status(PaymentStatus.ERROR)
                self.payment.message = json.dumps(_json)
                self.payment.save()
                return _json
            else:
                return {
                    'error' : -1 * response.status_code,
                    'error_note' : 'Http request error [{}]'.format(response.status_code)
                }
        else:
            return {
                'error' : -5002,
                'error_note' : 'Payment confirmed'
            }

    def payment_with_token(self):
        if self.payment.status != PaymentStatus.CONFIRMED:
            data = {
                "service_id": self.provider.merchant_service_id,
                "card_token": self.data['card_token'],
                "amount": self.payment.total,
                "merchant_trans_id": self.payment.transactions_id
            }
            if response.status_code == 200:
                _json = response.json()
                if _json['error_code'] == 0:
                    self.payment.change_status(PaymentStatus.CONFIRMED)
                else:
                    self.payment.change_status(PaymentStatus.ERROR)
                self.payment.message = json.dumps(_json)
                self.payment.save()
                return _json
            else:
                return {
                    'error' : -1 * response.status_code,
                    'error_note' : 'Http request error [{}]'.format(response.status_code)
                }
        else:
            return {
                'error' : -5002,
                'error_note' : 'Payment confirmed'
            }
    def delete_card_token(self):
        data = {
            'service_id' : self.provider.merchant_service_id,
            'card_token' : self.data['card_token']
        }
        response = requests.delete(self.endpoint + '/card_token/{service_id}/{card_token}'.format(**data))
        if response.status_code == 200:
            return response.json()
        return {
            'error' : -1 * response.status_code,
            'error_note' : 'Http request error [{}]'.format(response.status_code)
        }
    
class Services(ApiHelper):
    def __init__(self, data, service_type):
        self.data = data
        self.service_type = service_type
        self.payment_id = self.data.get('payment_id', None)
        self.provider = provider_factory('click')
        self.payment = get_object_or_404(get_payment_model(), id = self.payment_id)
        super(Services, self).__init__(self.provider, self.payment, self.data)
    
    def api(self):
        if self.service_type == 'create_invoice':
            return self.create_invoice()
        if self.service_type == 'check_invoice':
            return self.check_invoice()
        if self.service_type == 'create_card_token':
            return self.create_card_token()
        if self.service_type == 'verify_card_token':
            return self.verify_card_token()
        if self.service_type == 'payment_with_token':
            return self.payment_with_token()
        if self.service_type == 'delete_card_token':
            return self.delete_card_token()
        return {
            'error' : -1000,
            'error_note' : 'Service type could detect'
        }

class ClickProvider(BasicProvider):
    '''
    click.uz payment provider
    '''
    def __init__(self, merchant_id, merchant_service_id, merchant_user_id, secret_key, **kwargs):
        super(ClickProvider, self).__init__(**kwargs)
        self.merchant_id = merchant_id
        self.merchant_service_id = merchant_service_id
        self.merchant_user_id = merchant_user_id
        self.secret_key = secret_key
    
    def get_form(self, payment, data = None):
        if payment.status == PaymentStatus.WAITING:
            payment.change_status(PaymentStatus.INPUT)
        form = [
            PaymentPhoneNumberForm(provider = self, payment = payment),
            PaymentCardNumberForm(provider = self, payment = payment),
            PaymentButtonForm(provider = self, payment = payment)
        ]
        return form
