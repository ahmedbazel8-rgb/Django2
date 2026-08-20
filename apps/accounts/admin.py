"""
إعدادات لوحة الإدارة لتطبيق accounts
Admin configuration for accounts app  
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, ProviderProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    إدارة المستخدمين في لوحة التحكم
    Custom User admin
    """
    list_display = ['username', 'email', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone', 'city']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات إضافية', {
            'fields': ('role', 'phone', 'city', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('معلومات إضافية', {
            'fields': ('email', 'role', 'phone', 'city', 'is_verified')
        }),
    )


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    """
    إدارة ملفات مقدمي الخدمات
    Provider profiles admin
    """
    list_display = ['user', 'specialization', 'experience_years', 'get_status_badge', 'average_rating', 
                    'completed_orders', 'is_available', 'created_at']
    list_filter = ['status', 'is_available', 'specialization', 'created_at']
    search_fields = ['user__username', 'user__email', 'specialization', 'bio']
    readonly_fields = ['total_orders', 'completed_orders', 'average_rating', 'created_at', 'updated_at']
    ordering = ['-average_rating', '-completed_orders']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('user', 'bio', 'profile_image')
        }),
        ('معلومات العمل', {
            'fields': ('specialization', 'experience_years', 'hourly_rate', 'status', 'is_available')
        }),
        ('الموقع الجغرافي', {
            'fields': ('address', 'latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('الإحصائيات', {
            'fields': ('total_orders', 'completed_orders', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_providers', 'reject_providers']
    
    def get_status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
        }
        labels = dict(ProviderProfile.STATUS_CHOICES)
        return format_html('<span class="badge bg-{}">{}</span>', colors.get(obj.status, 'secondary'), labels.get(obj.status, obj.status))
    get_status_badge.short_description = 'حالة الحساب'
    
    def approve_providers(self, request, queryset):
        """الموافقة على مقدمي الخدمات المحددين"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'تم الموافقة على {updated} مقدم خدمة.')
    approve_providers.short_description = 'الموافقة على مقدمي الخدمات المحددين'
    
    def reject_providers(self, request, queryset):
        """رفض مقدمي الخدمات المحددين"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'تم رفض {updated} مقدم خدمة.')
    reject_providers.short_description = 'رفض مقدمي الخدمات المحددين'
