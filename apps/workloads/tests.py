from django.test import TestCase
from .models import Workload

class WorkloadModelTest(TestCase):
    def setUp(self):
        Workload.objects.create(
            user_id=1,
            project_id=1,
            department_id=1,
            year_month='2023-10',
            day_01=8,
            day_02=0,
            total_hours=8,
            total_days=1
        )

    def test_workload_creation(self):
        workload = Workload.objects.get(year_month='2023-10')
        self.assertEqual(workload.total_hours, 8)
        self.assertEqual(workload.total_days, 1)

    def test_workload_day_entries(self):
        workload = Workload.objects.get(year_month='2023-10')
        self.assertEqual(workload.day_01, 8)
        self.assertEqual(workload.day_02, 0)

    def test_workload_str(self):
        workload = Workload.objects.get(year_month='2023-10')
        self.assertEqual(str(workload), f'Workload for {workload.year_month}')