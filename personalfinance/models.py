from django.db import models
from userprofile.models import UserProfile


class Transaction(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # default date is the current date
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    receipt = models.ImageField(upload_to="receipts/", blank=True, null=True)
    recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"Transaction - {self.amount} ({self.date})"


class Income(Transaction):
    source = models.CharField(max_length=100)

    def __str__(self):
        return f"Income - {self.amount} ({self.date}) - {self.source}"


class Expense(Transaction):
    EXPENSE_CATEGORY = [
        ("food", "Food"),
        ("transport", "Transport"),
        ("utilities", "Utilities"),
        ("housing", "Housing"),
        ("clothing", "Clothing"),
        ("health", "Health"),
        ("education", "Education"),
        ("entertainment", "Entertainment"),
        ("others", "Others"),
    ]
    category = models.CharField(max_length=100, choices=EXPENSE_CATEGORY)
    split = models.BooleanField(default=False)
    divisions = models.IntegerField(default=1)
    recovered = models.IntegerField(default=1)
    def __str__(self):
        return f"Expense - {self.amount} ({self.date}) - {self.category}"


class Budget(models.Model):
    PERIOD_TYPE = [("weekly", "Weekly"), ("monthly", "Monthly"), ("yearly", "Yearly")]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, choices=Expense.EXPENSE_CATEGORY)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_TYPE)

    def __str__(self):
        return f"Budget - {self.amount} ({self.period}) - {self.category}"
