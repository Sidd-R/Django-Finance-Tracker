# views.py
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import datetime
from .models import Income, Expense
from django.db.models import Sum

def generate_graphs(expenses_by_category, income_by_month, expenses_by_month, savings_by_month):
    # Expenses by Category Pie Chart
    plt.figure(figsize=(6, 6))
    categories = [item['category'] for item in expenses_by_category]
    totals = [item['total'] for item in expenses_by_category]
    plt.pie(totals, labels=categories, autopct='%1.1f%%', startangle=140)
    plt.title('Expenses by Category')
    expenses_by_category_img = get_graph()

    # Monthly Income and Expenses Bar Chart
    plt.figure(figsize=(10, 6))
    months = [item['month'].strftime("%b %Y") for item in income_by_month]
    income_totals = [item['total'] for item in income_by_month]
    expenses_totals = [item['total'] for item in expenses_by_month]
    plt.bar(months, income_totals, label='Income', alpha=0.7, color='b')
    plt.bar(months, expenses_totals, label='Expenses', alpha=0.7, color='r', bottom=income_totals)
    plt.xticks(rotation=45)
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.title('Monthly Income and Expenses')
    plt.legend()
    monthly_income_expenses_img = get_graph()

    # Monthly Savings Bar Chart
    plt.figure(figsize=(10, 6))
    months = [item['month'].strftime("%b %Y") for item in savings_by_month]
    savings = [item['savings'] for item in savings_by_month]
    plt.bar(months, savings, color='g')
    plt.xticks(rotation=45)
    plt.xlabel('Month')
    plt.ylabel('Savings')
    plt.title('Monthly Savings')
    monthly_savings_img = get_graph()

    return expenses_by_category_img, monthly_income_expenses_img, monthly_savings_img

def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph