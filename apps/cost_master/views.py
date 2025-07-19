from django.shortcuts import render
from django.http import JsonResponse
from .models import CostMaster

def cost_master_list(request):
    costs = CostMaster.objects.all().values()
    return JsonResponse(list(costs), safe=False)

def cost_master_detail(request, pk):
    try:
        cost = CostMaster.objects.get(pk=pk)
        return JsonResponse(cost)
    except CostMaster.DoesNotExist:
        return JsonResponse({'error': 'Cost not found'}, status=404)

def cost_master_create(request):
    if request.method == 'POST':
        # Logic to create a new cost entry
        pass

def cost_master_update(request, pk):
    if request.method == 'PUT':
        # Logic to update an existing cost entry
        pass

def cost_master_delete(request, pk):
    if request.method == 'DELETE':
        try:
            cost = CostMaster.objects.get(pk=pk)
            cost.delete()
            return JsonResponse({'message': 'Cost deleted successfully'})
        except CostMaster.DoesNotExist:
            return JsonResponse({'error': 'Cost not found'}, status=404)