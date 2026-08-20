"""
النماذج (Models) لتطبيق Marketplace
Models for marketplace app - Categories and Services
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from apps.accounts.models import User


class Category(models.Model):
    """
    تصنيفات الخدمات (مع دعم التصنيفات الفرعية)
    Service categories with hierarchical support
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='اسم التصنيف'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    icon = models.CharField(
        max_length=50,
        default='bi-tag',
        verbose_name='الأيقونة',
        help_text='اسم أيقونة Bootstrap Icons (مثل: bi-laptop, bi-brush)'
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='التصنيف الأب'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name='الترتيب',
        help_text='الأرقام الأصغر تظهر أولاً'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التعديل'
    )
    
    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """رابط صفحة التصنيف"""
        return reverse('marketplace:category_detail', kwargs={'pk': self.pk})
    
    def get_services_count(self):
        """عدد الخدمات في هذا التصنيف"""
        return self.services.filter(status='active').count()
    
    def get_all_services_count(self):
        """عدد الخدمات شاملاً التصنيفات الفرعية"""
        count = self.get_services_count()
        for subcategory in self.subcategories.all():
            count += subcategory.get_all_services_count()
        return count


class Service(models.Model):
    """
    الخدمات المعروضة في السوق
    Services listed in the marketplace
    """
    
    PRICE_TYPE_CHOICES = [
        ('fixed', 'سعر ثابت'),
        ('hourly', 'بالساعة'),
        ('negotiable', 'قابل للتفاوض'),
    ]
    
    CURRENCY_CHOICES = [
        ('YER', 'ريال يمني'),
        ('SAR', 'ريال سعودي'),
        ('USD', 'دولار أمريكي'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('active', 'نشط'),
        ('paused', 'متوقف مؤقتاً'),
        ('closed', 'مغلق'),
    ]
    
    # العلاقات
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='services',
        limit_choices_to={'role': 'provider'},
        verbose_name='مقدم الخدمة'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='services',
        verbose_name='التصنيف'
    )
    
    # المعلومات الأساسية
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الخدمة'
    )
    
    description = models.TextField(
        verbose_name='وصف الخدمة',
        help_text='اشرح ما تقدمه في هذه الخدمة بالتفصيل'
    )
    
    # السعر
    price_type = models.CharField(
        max_length=20,
        choices=PRICE_TYPE_CHOICES,
        default='fixed',
        verbose_name='نوع السعر'
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='YER',
        verbose_name='العملة'
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='السعر',
        help_text='اترك فارغاً إذا كان قابل للتفاوض'
    )
    
    delivery_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='مدة التسليم (بالأيام)',
        help_text='كم يوماً تحتاج لإنجاز هذه الخدمة؟'
    )
    
    # الوسائط
    image = models.ImageField(
        upload_to='services/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='صورة الخدمة'
    )
    
    # الحالة
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة'
    )
    
    # الإحصائيات
    views_count = models.IntegerField(
        default=0,
        verbose_name='عدد المشاهدات'
    )
    
    orders_count = models.IntegerField(
        default=0,
        verbose_name='عدد الطلبات'
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='متوسط التقييم'
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name='خدمة مميزة',
        help_text='ستظهر في الصفحة الرئيسية'
    )
    
    # التواريخ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التعديل'
    )
    
    class Meta:
        verbose_name = 'خدمة'
        verbose_name_plural = 'الخدمات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['provider', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """رابط صفحة الخدمة"""
        return reverse('marketplace:service_detail', kwargs={'pk': self.pk})
    
    def increment_views(self):
        """زيادة عداد المشاهدات"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def get_price_display(self):
        """عرض السعر بشكل مناسب"""
        # رموز العملات
        currency_symbols = {
            'YER': 'ريال يمني',
            'SAR': 'ريال سعودي',
            'USD': 'دولار',
        }
        currency_text = currency_symbols.get(self.currency, self.currency)
        
        if self.price_type == 'negotiable':
            return 'قابل للتفاوض'
        elif self.price_type == 'hourly':
            return f'{self.price} {currency_text}/ساعة' if self.price else 'قابل للتفاوض'
        else:  # fixed
            return f'{self.price} {currency_text}' if self.price else 'قابل للتفاوض'
    
    def is_owned_by(self, user):
        """تحقق إذا كان المستخدم هو المالك"""
        return self.provider == user
