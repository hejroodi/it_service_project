from django.urls import path
from . import views

urlpatterns = [
    path('role_redirect/', views.role_redirect, name='role_redirect'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('user/new/', views.new_request, name='new_request'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/assign/<int:ticket_id>/', views.assign_expert, name='assign_expert'),
    path('expert/', views.expert_dashboard, name='expert_dashboard'),
    path('expert/done/<int:ticket_id>/', views.mark_done, name='mark_done'),
    path('manager/reports/', views.manager_reports, name='manager_reports'),
    path('manager/table/', views.manager_dashboard_table, name='manager_dashboard_table'),
    path('expert/table/', views.expert_dashboard_table, name='expert_dashboard_table'),
    path('user/table/', views.user_dashboard_table, name='user_dashboard_table'),
    path('manager/check-new/', views.check_new_tickets, name='check_new_tickets'),
    path('expert/check-new/', views.check_new_expert_tickets, name='check_new_expert_tickets'),
    path('expert/mark-notified/<int:ticket_id>/', views.mark_expert_notified, name='mark_expert_notified'),

]