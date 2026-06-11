from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
