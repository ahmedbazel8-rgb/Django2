"""
النماذج (Models) لتطبيق Orders
Models for orders app - Orders, Milestones, Deliveries, Messages
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from apps.accounts.models import User
from apps.marketplace.models import Service
import uuid
from datetime import timedelta


class Order(models.Model):
    """
    الطلبات - العقود بين العملاء ومقدمي الخدمات
    Orders - Contracts between customers and providers
    """
    
    STATUS_CHOICES = [
        ('pending', 'في انتظار الموافقة'),
        ('accepted', 'مقبول'),
        ('in_progress', 'قيد التنفيذ'),
        ('delivered', 'تم التسليم'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
        ('disputed', 'متنازع عليه'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('paid', 'مدفوع'),
        ('refunded', 'مسترد'),
    ]
    
    # العلاقات
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_customer',
        limit_choices_to={'role': 'customer'},
        verbose_name='العميل'
    )
    
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_provider',
        limit_choices_to={'role': 'provider'},
        verbose_name='مقدم الخدمة'
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name='الخدمة'
    )
    
    # المعلومات الأساسية
    order_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='رقم الطلب'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الطلب'
    )
    
    description = models.TextField(
        verbose_name='تفاصيل ومتطلبات الطلب',
        help_text='اشرح ما تريده بالتفصيل'
    )
    
    # التسعير والوقت
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='السعر المتفق عليه (ريال)'
    )
    
    delivery_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='مدة التسليم (بالأيام)'
    )
    
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التسليم المتوقع'
    )
    
    # الحالات
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الطلب'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='حالة الدفع'
    )
    
    # التواريخ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ القبول'
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ البدء'
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ التسليم'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال'
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإلغاء'
    )
    
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name='سبب الإلغاء'
    )
    
    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        """توليد رقم طلب فريد تلقائياً"""
        if not self.order_number:
            # تنسيق: ORD-2024-XXXXX
            year = timezone.now().year
            random_part = str(uuid.uuid4().int)[:5]
            self.order_number = f"ORD-{year}-{random_part}"
            
            # التأكد من أن الرقم فريد
            while Order.objects.filter(order_number=self.order_number).exists():
                random_part = str(uuid.uuid4().int)[:5]
                self.order_number = f"ORD-{year}-{random_part}"
        
        # حساب تاريخ التسليم المتوقع
        if not self.expected_delivery_date and self.accepted_at and self.delivery_days:
            self.expected_delivery_date = (self.accepted_at + timedelta(days=self.delivery_days)).date()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """رابط صفحة الطلب"""
        return reverse('orders:order_detail', kwargs={'order_number': self.order_number})
    
    def can_be_cancelled(self):
        """هل يمكن إلغاء الطلب؟"""
        return self.status in ['pending', 'accepted']
    
    def can_be_accepted(self):
        """هل يمكن قبول الطلب؟"""
        return self.status == 'pending'
    
    def can_be_started(self):
        """هل يمكن بدء العمل؟"""
        return self.status == 'accepted'
    
    def can_be_delivered(self):
        """هل يمكن التسليم؟"""
        return self.status == 'in_progress'
    
    def can_be_completed(self):
        """هل يمكن إكمال الطلب؟"""
        return self.status == 'delivered'
    
    def is_active(self):
        """هل الطلب نشط (غير منتهي)؟"""
        return self.status not in ['completed', 'cancelled', 'disputed']
    
    def get_status_badge_class(self):
        """الحصول على class للـ badge حسب الحالة"""
        status_classes = {
            'pending': 'bg-warning',
            'accepted': 'bg-info',
            'in_progress': 'bg-primary',
            'delivered': 'bg-success',
            'completed': 'bg-success',
            'cancelled': 'bg-secondary',
            'disputed': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_payment_badge_class(self):
        """الحصول على class للـ badge حسب حالة الدفع"""
        payment_classes = {
            'pending': 'bg-warning',
            'paid': 'bg-success',
            'refunded': 'bg-secondary',
        }
        return payment_classes.get(self.payment_status, 'bg-secondary')


class Milestone(models.Model):
    """
    معالم المشروع - تقسيم العمل لمراحل
    Project milestones
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='الطلب'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان المرحلة'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name='نسبة الإنجاز (%)'
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name='مكتملة'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإكمال'
    )
    
    order_index = models.IntegerField(
        default=0,
        verbose_name='الترتيب'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'معلم'
        verbose_name_plural = 'المعالم'
        ordering = ['order', 'order_index']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.title}"


class Delivery(models.Model):
    """
    التسليمات - الملفات والأعمال المسلمة
    Deliverables - Files and work delivered
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='الطلب'
    )
    
    file = models.FileField(
        upload_to='deliveries/%Y/%m/',
        verbose_name='ملف التسليم'
    )
    
    description = models.TextField(
        verbose_name='وصف التسليم',
        help_text='اشرح ما تم إنجازه'
    )
    
    delivered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التسليم'
    )
    
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='مقبول'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ المراجعة'
    )
    
    review_note = models.TextField(
        blank=True,
        verbose_name='ملاحظات المراجعة'
    )
    
    class Meta:
        verbose_name = 'تسليم'
        verbose_name_plural = 'التسليمات'
        ordering = ['-delivered_at']
    
    def __str__(self):
        return f"تسليم - {self.order.order_number}"


class OrderMessage(models.Model):
    """
    رسائل الطلب - التواصل بين العميل والمقدم حول الطلب
    Order messages - Communication about the order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='الطلب'
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='order_messages',
        verbose_name='المرسل'
    )
    
    message = models.TextField(
        verbose_name='الرسالة'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإرسال'
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name='مقروءة'
    )
    
    class Meta:
        verbose_name = 'رسالة طلب'
        verbose_name_plural = 'رسائل الطلبات'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.order.order_number}"
