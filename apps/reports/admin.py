from django.contrib import admin
from .models import ReportExport

class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('exported_by', 'year_month', 'department', 'format', 'exported_at')
    list_filter = ('format', 'exported_at', 'department')
    search_fields = ('year_month', 'exported_by__username')

admin.site.register(ReportExport, ReportExportAdmin)