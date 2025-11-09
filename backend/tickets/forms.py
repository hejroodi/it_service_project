from django import forms
from .models import Ticket
from django import forms
from .models import User, TicketMessage   # ← اینجا اضافه کن TicketMessage

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'unit', 'service_type']



# backend/tickets/forms.py
from django import forms
from .models import User

class FileSendForm(forms.Form):
    receiver = forms.ModelChoiceField(queryset=User.objects.all(), label="گیرنده فایل")
    file = forms.FileField(label="انتخاب فایل")

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 10 * 1024 * 1024:  # محدودیت 10MB
            raise forms.ValidationError("حداکثر حجم مجاز 10MB است.")
        return file

from django import forms
from .models import User

from django import forms
from .models import User

class UserContactForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['room_number', 'phone_number']
        labels = {
            'room_number': 'شماره اتاق',
            'phone_number': 'شماره تلفن اتاق'
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        
        # اگر کاربر چیزی وارد نکرد
        if not phone:
            raise forms.ValidationError("لطفا شماره تلفن را وارد کنید.")
        
        # فقط عدد باشد
        if not phone.isdigit():
            raise forms.ValidationError("شماره تلفن باید فقط شامل عدد باشد.")
        
        # طول دقیقاً 8 رقم باشد
        if len(phone) != 8:
            raise forms.ValidationError("شماره تلفن باید دقیقاً 8 رقم باشد.")
        
        return phone


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        labels = {
            'message': 'متن پیام'
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'پیام خود را بنویسید...'})
        }