from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Workload
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.generic import TemplateView

class WorkloadListView(TemplateView):
    template_name = "workloads/list.html"

@csrf_exempt
def workload_list(request):
    if request.method == 'GET':
        workloads = Workload.objects.all().values()
        return JsonResponse(list(workloads), safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        workload = Workload.objects.create(
            user_id=data['user_id'],
            project_id=data['project_id'],
            department_id=data['department_id'],
            year_month=data['year_month'],
            day_01=data['day_01'],
            day_02=data['day_02'],
            day_03=data['day_03'],
            # Add fields for day_04 to day_31 as needed
            total_hours=data['total_hours'],
            total_days=data['total_days']
        )
        return JsonResponse({'id': workload.id}, status=201)

@csrf_exempt
def workload_detail(request, pk):
    workload = get_object_or_404(Workload, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'user_id': workload.user_id,
            'project_id': workload.project_id,
            'department_id': workload.department_id,
            'year_month': workload.year_month,
            'day_01': workload.day_01,
            'day_02': workload.day_02,
            'day_03': workload.day_03,
            # Add fields for day_04 to day_31 as needed
            'total_hours': workload.total_hours,
            'total_days': workload.total_days
        })

    elif request.method == 'PUT':
        data = json.loads(request.body)
        workload.user_id = data['user_id']
        workload.project_id = data['project_id']
        workload.department_id = data['department_id']
        workload.year_month = data['year_month']
        workload.day_01 = data['day_01']
        workload.day_02 = data['day_02']
        workload.day_03 = data['day_03']
        # Update fields for day_04 to day_31 as needed
        workload.total_hours = data['total_hours']
        workload.total_days = data['total_days']
        workload.save()
        return JsonResponse({'id': workload.id})

    elif request.method == 'DELETE':
        workload.delete()
        return JsonResponse({'message': 'Workload deleted'}, status=204)