from django.shortcuts import render
from django.http import HttpResponse
from .models import Report

def report_list(request):
    reports = Report.objects.all()
    return render(request, 'reports/report_list.html', {'reports': reports})

def report_detail(request, report_id):
    report = Report.objects.get(id=report_id)
    return render(request, 'reports/report_detail.html', {'report': report})

def generate_report(request):
    # Logic for generating reports will go here
    return HttpResponse("Report generated successfully.")