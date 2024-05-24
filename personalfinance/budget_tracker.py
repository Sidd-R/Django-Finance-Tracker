from .models import Expense, Budget
from datetime import datetime
from django.core.mail import send_mail


def calculateExpenseByPeriod(user, period, date, category):
    expense_amount = 0

    if period == Budget.PERIOD_TYPE[0][0]:  # Weekly
        # get the week number in the year
        week_number = date.isocalendar()[1]

        # get all expenses in the week
        expenses_week = Expense.objects.filter(
            user=user, date__week=week_number, category=category
        )
        expense_amount = sum([expense.amount for expense in expenses_week])

    elif period == Budget.PERIOD_TYPE[1][0]:  # Monthly
        # get all expenses in the month
        expenses_month = Expense.objects.filter(
            user=user, date__month=date.month, category=category
        )
        expense_amount = sum([expense.amount for expense in expenses_month])

    elif period == Budget.PERIOD_TYPE[2][0]:  # Yearly
        # get all expenses in the year
        expenses_year = Expense.objects.filter(
            user=user, date__year=date.year, category=category
        )
        expense_amount = sum([expense.amount for expense in expenses_year])

    return expense_amount


def hasBudgetExceeded(user, expense):
    """returns List of budgets exceeded

    Keyword arguments:
    user -- user object from request
    expense -- expense object which was created
    Return: List
    """

    # get budgets for the expense category
    budgets = Budget.objects.filter(user=user, category=expense.category)

    budgets_exceeded = []
    
    alert_message_text = "Budget Exceeded Alert"
    alert_message_html = """
        <h1> Budget Exceeded Alert </h1>
        """
        
    for budget in budgets:
        if calculateExpenseByPeriod(user, budget.period, expense.date, expense.category) > budget.amount:
            budgets_exceeded.append(budget)
            alert_message_html  += f"<h3>{budget.period}  budget for {budget.category} exceeded </h3>"
            alert_message_text += f"\n{budget.period}  budget for {budget.category} exceeded"
    if budgets_exceeded:       
        send_mail(
            "Budget Exceeded",
            alert_message_text,
            "alert@personalfinancetracker.com",
            [user.email],
            html_message=alert_message_html,
            fail_silently=True
        )

    return budgets_exceeded
