from django.contrib import admin
from .models import Income, Expense, Budget #Investment

# Register your models here.
admin.site.register(Income)
admin.site.register(Expense)
# admin.site.register(Investment)
admin.site.register(Budget)
