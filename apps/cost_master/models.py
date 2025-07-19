from django.db import models
from django.utils import timezone

class CostMaster(models.Model):
    name = models.CharField(max_length=100, default='Unknown')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Cost Master'
        verbose_name_plural = 'Cost Masters'