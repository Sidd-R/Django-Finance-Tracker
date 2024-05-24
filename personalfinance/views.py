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


@login_required
def dashboard(request):
    return render(request, "dashboard.html",{
        "title": "Dashboard"
    
    })


@login_required
def incomes(request):
    context = {}
    print(request.user)
    income = Income.objects.filter(user=request.user)
    context["incomes"] = income
    context["title"] = "Income"

    return render(request, "income.html", context)


@login_required
def expenses(request):
    context = {}

    expense = Expense.objects.filter(user=request.user)
    context["expenses"] = expense
    context["title"] = "Expense"

    return render(request, "expense.html", context)


@login_required
def edit_income(request, id):
    context = {}
    income = Income.objects.get(id=id)
    context["income"] = income
    context["title"] = "Edit Income"

    return render(request, "edit_income.html", context)


@login_required
def edit_expense(request, id):
    context = {}
    expense = Expense.objects.get(id=id)
    context["expense"] = expense
    context["title"] = "Edit Expense"

    return render(request, "edit_expense.html", context)


# drf views
class IncomeView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "income.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk=None):
        context = {}
        incomes = Income.objects.filter(user=request.user)
        paginator = Paginator(incomes, 7)
        page = request.GET.get("page")
        total_items = len(incomes)
        
        try:
            incomes = paginator.page(page)
        except PageNotAnInteger:
            incomes = paginator.page(1)
            page = 1
        except EmptyPage:
            incomes = paginator.page(paginator.num_pages)
            
        start_item = (int(page) - 1) * 7
        end_item = start_item + 7
        
        if end_item > total_items:
            end_item = total_items
        
        start_item += 1
            
        no_of_pages = paginator.num_pages
        
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

    def get_object(self, pk):
        try:
            return Income.objects.get(pk=pk)
        except Income.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        income = self.get_object(pk)
        print(income)
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

class ExpenseView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "expense.html"
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/accounts/")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        context = {}
        expenses = Expense.objects.filter(user=request.user)
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
        print(request.user)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    "expenses": Expense.objects.filter(user=request.user),
                    "title": "Expense",
                }
            )

        return Response(serializer.errors, status=400)

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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


class IncomeViewSet(viewsets.ModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)