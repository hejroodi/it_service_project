from django.db import models
from django.contrib.auth.models import AbstractUser

ROLE_CHOICES = (
    ('user', 'کاربر عادی'),
    ('manager', 'مدیر IT'),
    ('expert', 'کارشناس IT'),
)

class Unit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

STATUS_CHOICES = (
    ('new', 'جدید'),
    ('in_progress', 'در حال انجام'),
    ('done', 'انجام شده'),
    ('cancelled', 'لغو شده'),
)

class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notified_to_expert = models.BooleanField(default=False)  # آیا هشدار برای کارشناس نمایش داده شده؟

class TicketFeedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)