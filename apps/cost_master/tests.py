from django.test import TestCase
from .models import CostMaster  # Adjust the import based on your actual model name

class CostMasterModelTests(TestCase):

    def setUp(self):
        # Set up any initial data for the tests
        self.cost_master = CostMaster.objects.create(
            # Initialize with appropriate fields
            name="Test Cost",
            amount=1000,
            # Add other fields as necessary
        )

    def test_cost_master_creation(self):
        """Test that a CostMaster instance is created correctly."""
        self.assertEqual(self.cost_master.name, "Test Cost")
        self.assertEqual(self.cost_master.amount, 1000)

    def test_cost_master_str(self):
        """Test the string representation of the CostMaster."""
        self.assertEqual(str(self.cost_master), "Test Cost")  # Adjust based on your __str__ method

    # Add more tests as necessary for your functionality