from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Expense, Income, Budget
from .serializers import ExpenseSerializer, IncomeSerializer, BudgetSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import authentication
from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from django.http import Http404, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .budget_tracker import hasBudgetExceeded
from django.db.models import F
from datetime import datetime, timedelta, date
from django.db.models import Sum
from django.db.models.functions import TruncMonth

@login_required
def dashboard(request):
    # Calculate total income and expenses
    total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0

    # Group expenses by category
    expenses_by_category = Expense.objects.values('category').annotate(total=Sum('amount')).order_by('-total')

    # Calculate monthly income and expenses for the last 6 months
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    income_by_month = Income.objects.filter(date__gte=six_months_ago).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')
    expenses_by_month = Expense.objects.filter(date__gte=six_months_ago).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'expenses_by_category': expenses_by_category,
        'income_by_month': income_by_month,
        'expenses_by_month': expenses_by_month,
    }
    return render(request, 'dashboard.html', context)


# drf views
class IncomeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "income.html"
    permission_classes = [IsAuthenticated]

    def dispatch(
        self, request, *args, **kwargs
    ):  # redirect to login page if user is not authenticated
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        context = {}
        # sort by created_at in descending order then date in descending order
        incomes = Income.objects.filter(user=request.user).order_by('-created_at','-date')
        paginator = Paginator(incomes, 7)
        page = request.GET.get("page")
        total_items = len(incomes)  # total number of items

        try:
            incomes = paginator.page(page)
        except PageNotAnInteger:
            incomes = paginator.page(1)
            page = 1
        except EmptyPage:
            incomes = paginator.page(paginator.num_pages)

        start_item = (int(page) - 1) * 7  # first item on the page
        end_item = start_item + 7  # last item on the page

        if end_item > total_items:
            end_item = total_items

        start_item += 1

        no_of_pages = paginator.num_pages
        
        # get dues
        context["dues"] = Expense.objects.filter(user=request.user, split=True).exclude(recovered=F('divisions')).order_by('date')

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


class EditIncomeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_income.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

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
class ExpenseView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "expense.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, budget_exceeded=None):
        context = {}
        expenses = Expense.objects.filter(user=request.user).order_by('-created_at','-date')
        paginator = Paginator(expenses, 7)
        page = request.GET.get("page")
        total_items = len(expenses)

        try:
            expenses = paginator.page(page)
        except PageNotAnInteger:
            expenses = paginator.page(1)
            page = 1
        except EmptyPage:
            expenses = paginator.page(paginator.num_pages)

        start_item = (int(page) - 1) * 7
        end_item = start_item + 7

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
            return self.get(request,budget_exceeded)

        return Response(serializer.errors, status=400)


class EditExpenseView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_expense.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

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


class BudgetView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "budget.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

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
        print(serializer.errors)
        return Response(serializer.errors, status=400)


class EditBudgetView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "edit_budget.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

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
    # form data
    multiple = request.POST.get('multiple')
    print(request.POST)
    if multiple:
        amount = (expense.divisions - expense.recovered)*expense.amount/expense.divisions
        expense.recovered = expense.divisions
    else:
        amount = expense.amount/expense.divisions
        expense.recovered += 1    
        
    income = Income.objects.create(
        user = expense.user,
        amount = amount,
        source = "Recovery of expense: "+expense.description,
        date = datetime.now()
    )
    income.save()
    
    expense.save()
    return redirect("income")