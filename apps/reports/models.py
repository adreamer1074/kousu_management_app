from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ReportExport(models.Model):
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='report_exports')
    exported_at = models.DateTimeField(auto_now_add=True)
    year_month = models.CharField(max_length=7)
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, related_name='report_exports')
    file_path = models.CharField(max_length=255)
    format = models.CharField(max_length=10)  # Excel, PDFなど

    def __str__(self):
        return f"Report {self.year_month} - {self.format}"