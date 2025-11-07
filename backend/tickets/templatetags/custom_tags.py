from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    چک می‌کند آیا کاربر داخل گروه مشخص شده هست یا نه
    در قالب:  {% if user|has_group:"User" %}
    """
    return user.groups.filter(name=group_name).exists()