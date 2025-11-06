from django.contrib import admin
from .models import Unit, User, ServiceType, Ticket, TicketFeedback

admin.site.register(Unit)
admin.site.register(User)
admin.site.register(ServiceType)
admin.site.register(Ticket)
admin.site.register(TicketFeedback)