from datetime import datetime, timedelta, date
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string, get_template
from io import BytesIO
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from xhtml2pdf import pisa
from .serializers import ExpenseSerializer, IncomeSerializer, BudgetSerializer
from .models import Expense, Income, Budget
from .budget_tracker import hasBudgetExceeded
from .report_generator import generate_graphs

@login_required
def dashboard(request):
    # Calculate total income and expenses
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0

    # Group expenses by category
    expenses_by_category = (
        Expense.objects.values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # Calculate monthly income and expenses for the last 6 months
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    income_by_month = (
        Income.objects.filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    expenses_by_month = (
        Expense.objects.filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    # Calculate monthly savings for the last 6 months
    savings_by_month = []
    months = [six_months_ago + timedelta(days=30 * (i + 1)) for i in range(6)]
    for month in months:
        income = (
            Income.objects.filter(
                date__year=month.year, date__month=month.month
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expenses = (
            Expense.objects.filter(
                date__year=month.year, date__month=month.month
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        savings_by_month.append({"month": month, "savings": income - expenses})

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "expenses_by_category": expenses_by_category,
        "income_by_month": income_by_month,
        "expenses_by_month": expenses_by_month,
        "savings_by_month": savings_by_month,
    }
    return render(request, "dashboard.html", context)


# drf views
class IncomeView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "income.html"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        context = {}
        # sort by created_at in descending order then date in descending order
        incomes = Income.objects.filter(user=request.user).order_by(
            "-created_at", "-date"
        )
        no_items_in_page = 6  # number of items in a page

        paginator = Paginator(incomes, no_items_in_page)
        page = request.GET.get("page")
        total_items = len(incomes)  # total number of items

        try:
            incomes = paginator.page(page)
        except PageNotAnInteger:
            incomes = paginator.page(1)
            page = 1
        except EmptyPage:
            incomes = paginator.page(paginator.num_pages)

        start_item = (int(page) - 1) * no_items_in_page  # first item on the page
        end_item = start_item + no_items_in_page  # last item on the page

        if end_item > total_items:
            end_item = total_items

        start_item += 1

        no_of_pages = paginator.num_pages

        # get dues
        context["dues"] = (
            Expense.objects.filter(user=request.user, split=True)
            .exclude(recovered=F("divisions"))
            .order_by("date")
        )

        context["transactions"] = incomes
        context["title"] = "Income"
        context["no_of_pages"] = no_of_pages
        context["page"] = page
        context["total_items"] = total_items
        context["start_item"] = start_item
        context["end_item"] = end_item
        return Response(context)

    def post(self, request):
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.get(request)
        return Response(serializer.errors, status=400)


class EditIncomeView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_income.html"
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):  # get the income object with the given pk
        try:
            return Income.objects.get(pk=pk)
        except Income.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        income = self.get_object(pk)
        return Response(
            {"transaction": income, "title": "Edit Income", "name": "income"}
        )

    def post(self, request, pk):
        if "_method" in request.POST and request.POST["_method"] == "PATCH":
            return self.patch(request, pk)
        income = self.get_object(pk)
        serializer = IncomeSerializer(income, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect("income")
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        income = self.get_object(pk)
        serializer = IncomeSerializer(income, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return redirect("income")
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        income = self.get_object(pk)
        income.delete()
        return HttpResponse(status=204)


# Expense views
class ExpenseView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "expense.html"
    permission_classes = [IsAuthenticated]

    def get(self, request, budget_exceeded=None):
        context = {}
        expenses = Expense.objects.filter(user=request.user).order_by(
            "-created_at", "-date"
        )
        no_items_in_page = 6

        paginator = Paginator(expenses, no_items_in_page)
        page = request.GET.get("page")
        total_items = len(expenses)

        try:
            expenses = paginator.page(page)
        except PageNotAnInteger:
            expenses = paginator.page(1)
            page = 1
        except EmptyPage:
            expenses = paginator.page(paginator.num_pages)

        start_item = (int(page) - 1) * no_items_in_page
        end_item = start_item + no_items_in_page

        if end_item > total_items:
            end_item = total_items

        start_item += 1

        no_of_pages = paginator.num_pages

        if budget_exceeded:
            context["budget_exceeded"] = budget_exceeded

        context["transactions"] = expenses
        context["title"] = "Expense"
        context["no_of_pages"] = no_of_pages
        context["page"] = page
        context["total_items"] = total_items
        context["start_item"] = start_item
        context["end_item"] = end_item
        return Response(context)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            print(serializer.data)

            budget_exceeded = hasBudgetExceeded(request.user, serializer.instance)
            return self.get(request, budget_exceeded)

        return Response(serializer.errors, status=400)


class EditExpenseView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_expense.html"
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        expense = self.get_object(pk)
        print(expense)
        return Response(
            {"transaction": expense, "title": "Edit Expense", "name": "expense"}
        )

    def post(self, request, pk):
        if "_method" in request.POST and request.POST["_method"] == "PATCH":
            return self.patch(request, pk)
        expense = self.get_object(pk)
        serializer = ExpenseSerializer(expense, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect("expense")
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        expense = self.get_object(pk)
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return redirect("expense")
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        income = self.get_object(pk)
        income.delete()
        return HttpResponse(status=204)


class BudgetView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "budget.html"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        budgets = Budget.objects.filter(user=request.user)
        return Response({"budgets": budgets, "title": "Budget"})

    def post(self, request):
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"budgets": Budget.objects.filter(user=request.user), "title": "Budget"}
            )
        return Response(serializer.errors, status=400)


class EditBudgetView(LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_budget.html"
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Budget.objects.get(pk=pk)
        except Budget.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        budget = self.get_object(pk)
        print(budget)
        return Response({"budget": budget, "title": "Edit Budget", "name": "budget"})

    def post(self, request, pk):
        if "_method" in request.POST and request.POST["_method"] == "PATCH":
            return self.patch(request, pk)
        budget = self.get_object(pk)
        serializer = BudgetSerializer(budget, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect("budget")
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        budget = self.get_object(pk)
        serializer = BudgetSerializer(budget, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return redirect("budget")
        print(serializer.errors)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        budget = self.get_object(pk)
        budget.delete()
        return HttpResponse(status=204)


@login_required
def due_received(request, pk):
    if request.method != "POST":
        return HttpResponse(status=405)
    expense = Expense.objects.get(pk=pk)
    multiple = request.POST.get("multiple")
    
    if multiple:
        amount = (
            (expense.divisions - expense.recovered) * expense.amount / expense.divisions
        )
        expense.recovered = expense.divisions
    else:
        amount = expense.amount / expense.divisions
        expense.recovered += 1

    income = Income.objects.create(
        user=expense.user,
        amount=amount,
        source="Recovery of expense: " + expense.description,
        date=datetime.now(),
    )
    income.save()

    expense.save()
    return redirect("income")

@login_required
def reports(request): 
    if request.method == 'GET':
        return render(request, 'reports.html',{'title':'Reports'})
    elif request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # increment end_date month by 1
            # end_date = end_date + timedelta(days=30)
        except (ValueError, TypeError):
            return HttpResponse('Invalid date format. Please use YYYY-MM-DD.')

        # Calculate total income and expenses within the date range
        total_income = Income.objects.filter(date__range=(start_date, end_date)).aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = Expense.objects.filter(date__range=(start_date, end_date)).aggregate(total=Sum('amount'))['total'] or 0

        # Group expenses by category within the date range
        expenses_by_category = Expense.objects.filter(date__range=(start_date, end_date)).values('category').annotate(total=Sum('amount')).order_by('-total')

        # Calculate monthly income and expenses within the date range
        income_by_month = Income.objects.filter(date__range=(start_date, end_date)).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')
        expenses_by_month = Expense.objects.filter(date__range=(start_date, end_date)).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

        # Combine income and expense data for looping in template
        income_expense_data = list(zip(income_by_month, expenses_by_month))

        # Calculate monthly savings within the date range
        savings_by_month = []
        months = [start_date + timedelta(days=30 * i) for i in range((end_date - start_date).days // 30 + 1)]
        for month in months:
            income = Income.objects.filter(date__year=month.year, date__month=month.month).aggregate(total=Sum('amount'))['total'] or 0
            expenses = Expense.objects.filter(date__year=month.year, date__month=month.month).aggregate(total=Sum('amount'))['total'] or 0
            savings_by_month.append({'month': month, 'savings': income - expenses})

        # Generate graphs
        expenses_by_category_img, monthly_income_expenses_img, monthly_savings_img = generate_graphs(expenses_by_category, income_by_month, expenses_by_month, savings_by_month)

        context = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'expenses_by_category': expenses_by_category,
            'income_by_month': income_by_month,
            'expenses_by_month': expenses_by_month,
            'savings_by_month': savings_by_month,
            'expenses_by_category_img': expenses_by_category_img,
            'monthly_income_expenses_img': monthly_income_expenses_img,
            'monthly_savings_img': monthly_savings_img,
        }
        
        template = get_template('report_template.html')
        html = template.render(context)

        result = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{start_date}_to_{end_date}.pdf"'
        return response
    else:
        return HttpResponse('Method not allowed', status=405)
