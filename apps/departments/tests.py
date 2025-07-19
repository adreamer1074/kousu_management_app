from django.test import TestCase
from .models import Department

class DepartmentModelTest(TestCase):

    def setUp(self):
        Department.objects.create(name="Sales")
        Department.objects.create(name="Engineering")

    def test_department_creation(self):
        sales = Department.objects.get(name="Sales")
        engineering = Department.objects.get(name="Engineering")
        self.assertEqual(sales.name, "Sales")
        self.assertEqual(engineering.name, "Engineering")

    def test_department_str(self):
        department = Department(name="Marketing")
        self.assertEqual(str(department), "Marketing")