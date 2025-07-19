from django.contrib import admin
from .models import CostMaster

class CostMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost', 'valid_from', 'valid_to')
    list_filter = ('valid_from', 'valid_to')
    search_fields = ('name',)

admin.site.register(CostMaster, CostMasterAdmin)