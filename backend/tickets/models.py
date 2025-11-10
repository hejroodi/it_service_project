from django.db import models
from django.contrib.auth.models import AbstractUser

# -----------------------
# انتخاب نقش کاربر
# -----------------------
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
    room_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره اتاق")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره تلفن اتاق")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -----------------------
# وضعیت درخواست‌ها
# -----------------------
STATUS_CHOICES = (
    ('new', 'جدید'),
    ('in_progress', 'در حال انجام'),
    ('done', 'انجام شده'),
    ('cancelled', 'لغو شده'),
)

# -----------------------
# نوع ثبت درخواست (از کاربر یا برگشتی)
# -----------------------
RETURN_STATUS_CHOICES = (
    ('none', 'ثبت اولیه کاربر'),
    ('returned', 'برگشتی از کارشناس'),
)


class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        User,
        related_name='assigned_tickets',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notified_to_expert = models.BooleanField(default=False)
    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        default='none'
    )

    def __str__(self):
        return self.title


class TicketFeedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.ticket.title} by {self.user.username}"

# backend/tickets/models.py

class FileTransfer(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_files')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_files')
    file_path = models.CharField(max_length=255)  # مسیر فایل روی دیسک
    downloaded = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(verbose_name="پیغام")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # پیام خوانده شده یا نه

    def __str__(self):
        return f"Message from {self.sender} in Ticket {self.ticket.id}"


class Hardware(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hardwares')
    title = models.CharField(max_length=200)
    model = models.CharField(max_length=200, blank=True)
    brand = models.CharField(max_length=200, blank=True)
    asset_number = models.CharField(max_length=100, blank=True)  # شماره اموال

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class Software(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='softwares')
    title = models.CharField(max_length=200)
    version = models.CharField(max_length=100, blank=True)
    vendor = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


