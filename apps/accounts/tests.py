"""
اختبارات تطبيق accounts
Tests for accounts app
"""
from django.test import TestCase
from apps.accounts.models import User, ProviderProfile


class UserModelTest(TestCase):
    """اختبارات موديل User"""
    
    def test_user_creation_customer(self):
        """اختبار إنشاء مستخدم عميل"""
        user = User.objects.create_user(
            username='customer1',
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        self.assertEqual(user.username, 'customer1')
        self.assertEqual(user.role, 'customer')
        self.assertTrue(user.is_customer())
        self.assertFalse(user.is_provider())
    
    def test_user_creation_provider(self):
        """اختبار إنشاء مستخدم مقدم خدمة"""
        user = User.objects.create_user(
            username='provider1',
            email='provider@test.com',
            password='testpass123',
            role='provider'
        )
        self.assertEqual(user.username, 'provider1')
        self.assertEqual(user.role, 'provider')
        self.assertTrue(user.is_provider())
        self.assertFalse(user.is_customer())
    
    def test_provider_profile_auto_creation(self):
        """اختبار إنشاء ملف مقدم الخدمة تلقائياً"""
        provider = User.objects.create_user(
            username='provider1',
            email='provider@test.com',
            password='testpass123',
            role='provider'
        )
        self.assertTrue(hasattr(provider, 'provider_profile'))
        self.assertIsInstance(provider.provider_profile, ProviderProfile)
