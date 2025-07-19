from django.shortcuts import render, get_object_or_404
from .models import Project
from django.http import JsonResponse
from django.views import View

class ProjectListView(View):
    def get(self, request):
        projects = Project.objects.all()
        return render(request, 'projects/project_list.html', {'projects': projects})

class ProjectDetailView(View):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        return render(request, 'projects/project_detail.html', {'project': project})

class ProjectCreateView(View):
    def post(self, request):
        # Logic for creating a new project
        pass

class ProjectUpdateView(View):
    def post(self, request, pk):
        # Logic for updating an existing project
        pass

class ProjectDeleteView(View):
    def post(self, request, pk):
        # Logic for deleting a project
        pass

def project_api(request):
    projects = list(Project.objects.values())
    return JsonResponse(projects, safe=False)