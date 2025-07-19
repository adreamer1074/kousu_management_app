from django.test import TestCase
from .models import Permission  # Adjust the import based on your actual model

class PermissionModelTests(TestCase):

    def setUp(self):
        # Create a sample permission for testing
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='test_permission',
            # Add other fields as necessary
        )

    def test_permission_creation(self):
        """Test that the permission is created correctly."""
        self.assertEqual(self.permission.name, 'Test Permission')
        self.assertEqual(self.permission.codename, 'test_permission')

    def test_permission_str(self):
        """Test the string representation of the permission."""
        self.assertEqual(str(self.permission), 'Test Permission')  # Adjust based on your __str__ method

    # Add more tests as necessary for your permission functionality