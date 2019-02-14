from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import utils
from . import Services

@csrf_exempt
def prepare(request):
    return utils.prepare(request)

@csrf_exempt
def complete(request):
    return utils.complete(request)

@csrf_exempt
def service(request, service_type):
    service = Services(request.POST, service_type)
    return JsonResponse(service.api())