"""
موديلات المستخدمين والملفات الشخصية
User and Profile models for the accounts app
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    موديل المستخدم المخصص مع أدوار مختلفة
    Custom User model with role system
    """
    ROLE_CHOICES = (
        ('customer', 'عميل'),
        ('provider', 'مقدم خدمة'),
        ('admin', 'مدير'),#[;lg;gd;''s'f';]
    )
    
    # الحقول الأساسية
    email = models.EmailField('البريد الإلكتروني', unique=True)
    role = models.CharField('الدور', max_length=20, choices=ROLE_CHOICES, default='customer')
    
    
    # معلومات إضافية
    phone = models.CharField('رقم الجوال', max_length=20, blank=True)
    city = models.CharField('المدينة', max_length=100, blank=True)
    
    # حالة الحساب
    is_verified = models.BooleanField('حساب موثق', default=False)
    is_active = models.BooleanField('حساب نشط', default=True)
    
    # تواريخ
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    # استخدام email كاسم مستخدم
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_customer(self):
        """تحقق إذا كان المستخدم عميل"""
        return self.role == 'customer'
    
    def is_provider(self):
        """تحقق إذا كان المستخدم مقدم خدمة"""
        return self.role == 'provider'
    
    def is_admin_role(self):
        """تحقق إذا كان المستخدم مدير"""
        return self.role == 'admin' or self.is_superuser


class ProviderProfile(models.Model):
    """
    الملف الشخصي لمقدم الخدمة
    Provider profile with additional information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    
    # معلومات شخصية
    bio = models.TextField('نبذة تعريفية', max_length=500, blank=True)
    profile_image = models.ImageField('صورة الملف الشخصي', upload_to='profiles/', blank=True, null=True)
    
    # معلومات العمل
    specialization = models.CharField('التخصص', max_length=100, blank=True, 
                                     help_text='مثال: تصميم جرافيك، برمجة ويب، تسويق')
    experience_years = models.PositiveIntegerField('سنوات الخبرة', default=0)
    hourly_rate = models.DecimalField('السعر بالساعة', max_digits=10, decimal_places=2, 
                                      null=True, blank=True, help_text='بالريال اليمني')
    
    # موقع جغرافي
    address = models.TextField('العنوان', blank=True)
    latitude = models.DecimalField('خط العرض', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('خط الطول', max_digits=9, decimal_places=6, null=True, blank=True)
    
    # إحصائيات
    total_orders = models.PositiveIntegerField('إجمالي الطلبات', default=0)
    completed_orders = models.PositiveIntegerField('الطلبات المكتملة', default=0)
    average_rating = models.DecimalField('متوسط التقييم', max_digits=3, decimal_places=2, 
                                         default=0.00, help_text='من 0 إلى 5')
    
    # حالة
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    ]
    status = models.CharField('حالة الحساب', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_available = models.BooleanField('متاح لطلبات جديدة', default=True)
    
    # تواريخ
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        verbose_name = 'ملف مقدم خدمة'
        verbose_name_plural = 'ملفات مقدمي الخدمات'
        ordering = ['-average_rating', '-completed_orders']
    
    def __str__(self):
        return f"ملف {self.user.username}"
    
    def get_completion_rate(self):
        """حساب نسبة إتمام الطلبات"""
        if self.total_orders == 0:
            return 0
        return round((self.completed_orders / self.total_orders) * 100, 2)
    
    def update_stats(self):
        """تحديث الإحصائيات من الطلبات"""
        from apps.orders.models import Order
        orders = Order.objects.filter(provider=self.user)
        self.total_orders = orders.count()
        self.completed_orders = orders.filter(status='COMPLETED').count()
        self.save()
