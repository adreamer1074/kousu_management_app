from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Permission

@login_required
def permission_list(request):
    permissions = Permission.objects.all()
    return render(request, 'permissions/permission_list.html', {'permissions': permissions})

@login_required
def permission_detail(request, pk):
    permission = Permission.objects.get(pk=pk)
    return render(request, 'permissions/permission_detail.html', {'permission': permission})

@login_required
def permission_create(request):
    if request.method == 'POST':
        # Logic for creating a new permission
        pass
    return render(request, 'permissions/permission_form.html')

@login_required
def permission_update(request, pk):
    permission = Permission.objects.get(pk=pk)
    if request.method == 'POST':
        # Logic for updating the permission
        pass
    return render(request, 'permissions/permission_form.html', {'permission': permission})

@login_required
def permission_delete(request, pk):
    permission = Permission.objects.get(pk=pk)
    if request.method == 'POST':
        permission.delete()
        # Redirect to permission list
    return render(request, 'permissions/permission_confirm_delete.html', {'permission': permission})