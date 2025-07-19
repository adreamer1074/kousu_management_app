from django.db import models
from apps.users.models import CustomUser
from apps.departments.models import Department

AUTH_USER_MODEL = 'users.CustomUser'

class Project(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='projects')
    status = models.CharField(max_length=50)
    classification = models.CharField(max_length=50)
    estimate_date = models.DateField(null=True, blank=True)
    order_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    inspection_date = models.DateField(null=True, blank=True)
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    billing_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    outsourcing_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_workdays = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    used_workdays = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    newbie_workdays = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remaining_workdays = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wip_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    billing_destination = models.CharField(max_length=100, blank=True)
    billing_contact = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    mub_manager = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name