# ====================== Imports ======================
import os
from datetime import timedelta
from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from .forms import (
    UserContactForm,
    TicketForm,
    FileSendForm,
    TicketMessageForm
)
from .models import (
    Ticket,
    User,
    FileTransfer,
    Hardware,  
    Software 
)

# ====================== فایل‌ها ======================

@login_required
def send_file(request):
    """ارسال فایل از کاربر به کاربر دیگر"""
    if FileTransfer.objects.filter(sender=request.user, downloaded=False).exists():
        return redirect('user_dashboard')

    if request.method == "POST":
        form = FileSendForm(request.POST, request.FILES)
        if form.is_valid():
            receiver = form.cleaned_data['receiver']
            file_obj = form.cleaned_data['file']
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'tempfiles')
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file_obj.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            FileTransfer.objects.create(
                sender=request.user,
                receiver=receiver,
                file_path=file_path
            )
            return redirect('user_dashboard')
    else:
        form = FileSendForm()

    return render(request, 'tickets/send_file.html', {'form': form})


@login_required
def receive_file(request):
    """دریافت فایل و حذف بعد دانلود"""
    transfer = FileTransfer.objects.filter(receiver=request.user, downloaded=False).first()
    if not transfer:
        return redirect('user_dashboard')

    file_path = transfer.file_path
    if os.path.exists(file_path):
        transfer.downloaded = True
        transfer.save()
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        os.remove(file_path)  # حذف فایل بعد از دانلود
        return response

    return redirect('user_dashboard')

# ====================== هشدار به مدیر ======================

@login_required
def check_new_manager_tickets(request):
    tickets = Ticket.objects.filter(
        status='new',
        notified_to_manager=False
    ).values('id', 'title', 'status')
    return JsonResponse(list(tickets), safe=False)


@login_required
def mark_manager_notified(request, ticket_id):
    Ticket.objects.filter(id=ticket_id).update(notified_to_manager=True)
    return JsonResponse({"ok": True})

# ====================== کاربر ======================

@login_required
def user_dashboard(request):
    active_tickets = Ticket.objects.filter(requester=request.user).exclude(status='done').order_by('-created_at')
    done_tickets = Ticket.objects.filter(requester=request.user, status='done').order_by('-created_at')

    for t in list(active_tickets) + list(done_tickets):
        if t.assigned_to:
            t.before_count = Ticket.objects.filter(
                assigned_to=t.assigned_to,
                status__in=['new', 'in_progress'],
                created_at__lt=t.created_at
            ).count()
        else:
            t.before_count = None
        # محاسبه برای چشمک زدن گفت‌وگو
        t.has_unread = t.messages.filter(~Q(sender=request.user), is_read=False).exists()

    incoming_file = FileTransfer.objects.filter(receiver=request.user, downloaded=False).exists()
    outgoing_wait = FileTransfer.objects.filter(sender=request.user, downloaded=False).exists()
    managers = User.objects.filter(role='manager')

    # 👇 گرفتن سخت‌افزارها و نرم‌افزارهای کاربر
    hardwares = Hardware.objects.filter(user=request.user)
    softwares = Software.objects.filter(user=request.user)

    return render(request, 'tickets/user_dashboard.html', {
        'active_tickets': active_tickets,
        'done_tickets': done_tickets,
        'open_requests': active_tickets.count(),
        'closed_requests': done_tickets.count(),
        'total_requests': active_tickets.count() + done_tickets.count(),
        'incoming_file': incoming_file,
        'outgoing_wait': outgoing_wait,
        'managers': managers,
        'hardwares': hardwares,     # 👈 ارسال به قالب
        'softwares': softwares      # 👈 ارسال به قالب
    })


@login_required
def user_dashboard_table(request):
    active_tickets = Ticket.objects.filter(requester=request.user).exclude(status='done').order_by('-created_at')
    done_tickets = Ticket.objects.filter(requester=request.user, status='done').order_by('-created_at')

    for t in list(active_tickets) + list(done_tickets):
        if t.assigned_to:
            t.before_count = Ticket.objects.filter(
                assigned_to=t.assigned_to,
                status__in=['new', 'in_progress'],
                created_at__lt=t.created_at
            ).count()
        else:
            t.before_count = None
        t.has_unread = t.messages.filter(~Q(sender=request.user), is_read=False).exists()

    html_active = render_to_string('tickets/_user_table_active.html', {'tickets': active_tickets}, request=request)
    html_done = render_to_string('tickets/_user_table_done.html', {'tickets': done_tickets}, request=request)
    return JsonResponse({'html_active': html_active, 'html_done': html_done})


@login_required
def new_request(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.requester = request.user
            ticket.status = 'new'
            ticket.save()
            return redirect('user_dashboard')
    else:
        form = TicketForm()
    return render(request, 'tickets/request_form.html', {'form': form})


@login_required
def edit_request(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, requester=request.user)
    if ticket.status != 'new' or ticket.assigned_to is not None:
        messages.error(request, "این درخواست قابل ویرایش نیست.")
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "درخواست با موفقیت ویرایش شد.")
            return redirect('user_dashboard')
    else:
        form = TicketForm(instance=ticket)

    return render(request, 'tickets/request_form.html', {'form': form})


@login_required
def delete_request(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, requester=request.user)
    if ticket.status != 'new' or ticket.assigned_to is not None:
        messages.error(request, "این درخواست قابل حذف نیست.")
        return redirect('user_dashboard')

    ticket.delete()
    messages.success(request, "درخواست با موفقیت حذف شد.")
    return redirect('user_dashboard')

# ====================== مدیر IT ======================

@login_required
def manager_dashboard(request):
    new_from_user = Ticket.objects.filter(status='new', return_status='none').order_by('created_at')
    returned_from_expert = Ticket.objects.filter(status='new', return_status='returned').order_by('created_at')
    in_progress = Ticket.objects.filter(status='in_progress').order_by('created_at')
    done_tickets = Ticket.objects.filter(status='done').order_by('-created_at')
    experts = User.objects.filter(role='expert')

    return render(request, 'tickets/manager_dashboard.html', {
        'new_from_user': new_from_user,
        'returned_from_expert': returned_from_expert,
        'in_progress': in_progress,
        'done_tickets': done_tickets,
        'experts': experts
    })


@login_required
def manager_dashboard_table(request):
    new_from_user = Ticket.objects.filter(status='new', return_status='none').order_by('created_at')
    returned_from_expert = Ticket.objects.filter(status='new', return_status='returned').order_by('created_at')
    in_progress = Ticket.objects.filter(status='in_progress').order_by('created_at')
    done_tickets = Ticket.objects.filter(status='done').order_by('-created_at')
    experts = User.objects.filter(role='expert')

    html_new_user = render_to_string('tickets/_manager_table.html', {'tickets': new_from_user, 'experts': experts}, request=request)
    html_returned = render_to_string('tickets/_manager_table.html', {'tickets': returned_from_expert, 'experts': experts}, request=request)
    html_in_progress = render_to_string('tickets/_manager_table.html', {'tickets': in_progress, 'experts': experts}, request=request)
    html_done = render_to_string('tickets/_manager_table.html', {'tickets': done_tickets, 'experts': experts}, request=request)

    return JsonResponse({
        'html_new_user': html_new_user,
        'html_returned': html_returned,
        'html_in_progress': html_in_progress,
        'html_done': html_done
    })


@login_required
def assign_expert(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, id=ticket_id)
        expert_id = request.POST.get('expert_id')
        if expert_id:
            expert = get_object_or_404(User, id=expert_id)
            ticket.assigned_to = expert
            ticket.status = 'in_progress'
            ticket.save()
        return redirect('manager_dashboard')


@login_required
def manager_reports(request):
    status_counts = Ticket.objects.values('status').annotate(total=Count('id'))
    last_30_days = timezone.now() - timedelta(days=30)
    recent_tickets = Ticket.objects.filter(created_at__gte=last_30_days)
    unit_counts = recent_tickets.values('unit__name').annotate(total=Count('id'))

    return render(request, 'tickets/manager_reports.html', {
        'status_counts': status_counts,
        'unit_counts': unit_counts,
    })

# ====================== کارشناس IT ======================

@login_required
def expert_dashboard(request):
    active_tickets = Ticket.objects.filter(assigned_to=request.user, status__in=['new', 'in_progress']).order_by('created_at')
    done_tickets = Ticket.objects.filter(assigned_to=request.user, status='done').order_by('-created_at')

    for t in list(active_tickets) + list(done_tickets):
        t.has_unread = t.messages.filter(~Q(sender=request.user), is_read=False).exists()

    return render(request, 'tickets/expert_dashboard.html', {
        'active_tickets': active_tickets,
        'done_tickets': done_tickets,
        'open_requests': active_tickets.count(),
        'closed_requests': done_tickets.count(),
        'total_requests': active_tickets.count() + done_tickets.count()
    })


@login_required
def expert_dashboard_table(request):
    active_tickets = Ticket.objects.filter(assigned_to=request.user, status__in=['new', 'in_progress']).order_by('created_at')
    done_tickets = Ticket.objects.filter(assigned_to=request.user, status='done').order_by('-created_at')

    for t in list(active_tickets) + list(done_tickets):
        t.has_unread = t.messages.filter(~Q(sender=request.user), is_read=False).exists()

    html_active = render_to_string('tickets/_expert_table.html', {'tickets': active_tickets}, request=request)
    html_done = render_to_string('tickets/_expert_table.html', {'tickets': done_tickets}, request=request)

    return JsonResponse({'html_active': html_active, 'html_done': html_done})


@login_required
def mark_done(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, assigned_to=request.user)
    ticket.status = 'done'
    ticket.save()
    return redirect('expert_dashboard')


@login_required
def return_to_manager(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, assigned_to=request.user)
    if request.method == 'POST':
        ticket.assigned_to = None
        ticket.status = 'new'
        ticket.return_status = 'returned'
        ticket.save()
    return redirect('expert_dashboard')

# ====================== هدایت نقش ======================

@login_required
def role_redirect(request):
    if request.user.role == 'manager':
        return redirect('manager_dashboard')
    elif request.user.role == 'expert':
        return redirect('expert_dashboard')
    else:
        return redirect('user_dashboard')

# ====================== هشدارها ======================

@login_required
def check_new_expert_tickets(request):
    tickets = Ticket.objects.filter(
        assigned_to=request.user,
        status__in=['new', 'in_progress'],
        notified_to_expert=False
    ).values('id', 'title', 'status')
    return JsonResponse(list(tickets), safe=False)


@login_required
def mark_expert_notified(request, ticket_id):
    Ticket.objects.filter(
        id=ticket_id,
        assigned_to=request.user
    ).update(notified_to_expert=True)
    return JsonResponse({"ok": True})

# ====================== ویرایش اطلاعات تماس ======================

@login_required
def edit_contact_info(request):
    if request.method == "POST":
        form = UserContactForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات تماس شما با موفقیت ذخیره شد.")
            return redirect('user_dashboard')
    else:
        form = UserContactForm(instance=request.user)
    return render(request, 'tickets/edit_contact_info.html', {'form': form})

# ====================== گفت‌وگو ======================

@login_required
def ticket_messages(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # فقط صاحب یا کارشناس تیکت می‌توانند گفتگو کنند
    if request.user != ticket.requester and request.user != ticket.assigned_to:
        messages.error(request, "شما اجازه مشاهده این گفتگو را ندارید.")
        return redirect('role_redirect')

    if request.method == 'POST':
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.sender = request.user
            msg.save()

            if request.user == ticket.requester:
                return redirect('user_dashboard')
            elif request.user == ticket.assigned_to:
                return redirect('expert_dashboard')
            else:
                return redirect('role_redirect')
    else:
        form = TicketMessageForm()

    # پیام‌های خوانده‌نشده طرف مقابل را خوانده‌شده کن
    ticket.messages.filter(~Q(sender=request.user), is_read=False).update(is_read=True)
    messages_qs = ticket.messages.order_by('created_at')

    return render(request, 'tickets/ticket_messages.html', {
        'ticket': ticket,
        'form': form,
        'messages': messages_qs
    })