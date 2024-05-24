from django import template
import math

register = template.Library()

@register.simple_tag
def calculate_due_tag(amt, rec, div):
    # return upto 2 decimal places
    return math.ceil(amt * (div - rec) / div * 100) / 100    
