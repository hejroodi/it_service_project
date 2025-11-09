from django.urls import path
from . import views

urlpatterns = [
    # ---------- هدایت بر اساس نقش ----------
    path('role_redirect/', views.role_redirect, name='role_redirect'),

    # ---------- کاربر ----------
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('user/table/', views.user_dashboard_table, name='user_dashboard_table'),
    path('user/new/', views.new_request, name='new_request'),
    path('user/edit/<int:ticket_id>/', views.edit_request, name='edit_request'),
    path('user/delete/<int:ticket_id>/', views.delete_request, name='delete_request'),

    # ---------- مدیر IT ----------
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/table/', views.manager_dashboard_table, name='manager_dashboard_table'),
    path('manager/assign/<int:ticket_id>/', views.assign_expert, name='assign_expert'),
    path('manager/reports/', views.manager_reports, name='manager_reports'),

    # ---------- کارشناس ----------
    path('expert/', views.expert_dashboard, name='expert_dashboard'),
    path('expert/table/', views.expert_dashboard_table, name='expert_dashboard_table'),
    path('expert/done/<int:ticket_id>/', views.mark_done, name='mark_done'),
    path('expert/return/<int:ticket_id>/', views.return_to_manager, name='return_to_manager'),

    # ---------- هشدارها ----------
    path('manager/check-new/', views.check_new_manager_tickets, name='check_new_manager_tickets'),
    path('manager/mark-notified/<int:ticket_id>/', views.mark_manager_notified, name='mark_manager_notified'),
    path('expert/check-new/', views.check_new_expert_tickets, name='check_new_expert_tickets'),
    path('expert/mark-notified/<int:ticket_id>/', views.mark_expert_notified, name='mark_expert_notified'),
    # ---------- انتقال فایل ----------
    path('file/send/', views.send_file, name='send_file'),
   path('file/receive/', views.receive_file, name='receive_file'),
   path('user/contact/', views.edit_contact_info, name='edit_contact_info'),
   path('ticket/<int:ticket_id>/messages/', views.ticket_messages, name='ticket_messages'),
]
