from django.test import TestCase
from .models import Project

class ProjectModelTests(TestCase):

    def setUp(self):
        Project.objects.create(
            project_name="Test Project",
            case_name="Test Case",
            department_id=1,
            status="進行中",
            case_classification="開発",
            estimate_date="2025-01-01",
            order_date="2025-01-02",
            planned_end_date="2025-12-31",
            actual_end_date=None,
            inspection_date=None,
            budget_amount=1000000,
            billing_amount=800000,
            outsourcing_cost=200000,
            estimated_workdays=10,
            used_workdays=5,
            newbie_workdays=2,
            remaining_workdays=5,
            remaining_amount=200000,
            profit_rate=20,
            wip_amount=300000,
            billing_destination="Client A",
            billing_contact="Contact A",
            remarks="Test remarks",
            mub_manager="Manager A"
        )

    def test_project_creation(self):
        project = Project.objects.get(project_name="Test Project")
        self.assertEqual(project.case_name, "Test Case")
        self.assertEqual(project.status, "進行中")

    def test_project_remaining_workdays(self):
        project = Project.objects.get(project_name="Test Project")
        self.assertEqual(project.remaining_workdays, 5)

    def test_project_profit_rate(self):
        project = Project.objects.get(project_name="Test Project")
        self.assertEqual(project.profit_rate, 20)