from django.db import models
from django.contrib.auth.models import Group

class Permission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        unique_together = ('group', 'department')

    def __str__(self):
        return f"{self.group.name} - {self.department.name}"