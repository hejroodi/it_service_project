from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.http import JsonResponse
from itertools import chain

from .models import Ticket, User
from .forms import TicketForm

@login_required
def check_new_manager_tickets(request):
    tickets = Ticket.objects.filter(
        status='new',
        notified_to_manager=False  # فیلد جدید مثل notified_to_expert
    ).values('id', 'title', 'status')
    return JsonResponse(list(tickets), safe=False)

@login_required
def mark_manager_notified(request, ticket_id):
    Ticket.objects.filter(id=ticket_id).update(notified_to_manager=True)
    return JsonResponse({"ok": True})

# ---------- کاربر ----------
@login_required
def user_dashboard(request):
    tickets = Ticket.objects.filter(requester=request.user).order_by('-created_at')
    for t in tickets:
        if t.assigned_to:
            t.before_count = Ticket.objects.filter(
                assigned_to=t.assigned_to,
                status__in=['new', 'in_progress'],
                created_at__lt=t.created_at
            ).count()
        else:
            t.before_count = None
    return render(request, 'tickets/user_dashboard.html', {'tickets': tickets})

@login_required
def user_dashboard_table(request):
    tickets = Ticket.objects.filter(requester=request.user).order_by('-created_at')
    for t in tickets:
        if t.assigned_to:
            t.before_count = Ticket.objects.filter(
                assigned_to=t.assigned_to,
                status__in=['new', 'in_progress'],
                created_at__lt=t.created_at
            ).count()
        else:
            t.before_count = None
    html = render_to_string('tickets/_user_table.html', {'tickets': tickets}, request=request)
    return JsonResponse({'html': html})

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


# ---------- مدیر IT ----------
@login_required
def manager_dashboard(request):
    unassigned = Ticket.objects.filter(status='new').order_by('created_at')
    in_progress = Ticket.objects.filter(status='in_progress').order_by('created_at')
    done = Ticket.objects.filter(status='done').order_by('-created_at')
    tickets = list(chain(unassigned, in_progress, done))
    experts = User.objects.filter(role='expert')
    return render(request, 'tickets/manager_dashboard.html', {
        'tickets': tickets,
        'experts': experts
    })

@login_required
def manager_dashboard_table(request):
    unassigned = Ticket.objects.filter(status='new').order_by('created_at')
    in_progress = Ticket.objects.filter(status='in_progress').order_by('created_at')
    done = Ticket.objects.filter(status='done').order_by('-created_at')
    tickets = list(chain(unassigned, in_progress, done))
    experts = User.objects.filter(role='expert')
    html = render_to_string('tickets/_manager_table.html', {
        'tickets': tickets,
        'experts': experts
    }, request=request)
    return JsonResponse({'html': html})

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
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_tickets = Ticket.objects.filter(created_at__gte=thirty_days_ago)
    unit_counts = recent_tickets.values('unit__name').annotate(total=Count('id'))
    return render(request, 'tickets/manager_reports.html', {
        'status_counts': status_counts,
        'unit_counts': unit_counts,
    })


# ---------- کارشناس ----------
@login_required
def expert_dashboard(request):
    new_tickets = Ticket.objects.filter(assigned_to=request.user, status='new').order_by('created_at')
    in_progress_tickets = Ticket.objects.filter(assigned_to=request.user, status='in_progress').order_by('created_at')
    done_tickets = Ticket.objects.filter(assigned_to=request.user, status='done').order_by('-created_at')
    tickets = list(chain(new_tickets, in_progress_tickets, done_tickets))
    return render(request, 'tickets/expert_dashboard.html', {'tickets': tickets})

@login_required
def expert_dashboard_table(request):
    new_tickets = Ticket.objects.filter(assigned_to=request.user, status='new').order_by('created_at')
    in_progress_tickets = Ticket.objects.filter(assigned_to=request.user, status='in_progress').order_by('created_at')
    done_tickets = Ticket.objects.filter(assigned_to=request.user, status='done').order_by('-created_at')
    tickets = list(chain(new_tickets, in_progress_tickets, done_tickets))
    html = render_to_string('tickets/_expert_table.html', {'tickets': tickets}, request=request)
    return JsonResponse({'html': html})

@login_required
def mark_done(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, assigned_to=request.user)
    ticket.status = 'done'
    ticket.save()
    return redirect('expert_dashboard')


# ---------- هشدارها ----------
@login_required
def check_new_tickets(request):
    new_tickets_count = Ticket.objects.filter(status='new').count()
    return JsonResponse({"new_tickets": new_tickets_count})

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


# ---------- هدایت بر اساس نقش ----------
@login_required
def role_redirect(request):
    if request.user.role == 'manager':
        return redirect('manager_dashboard')
    elif request.user.role == 'expert':
        return redirect('expert_dashboard')
    else:
        return redirect('user_dashboard')