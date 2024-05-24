from django.urls import path, include
from . import views
from django.views.generic.base import RedirectView
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'expense', views.ExpenseViewSet)
router.register(r'income', views.IncomeViewSet)
router.register(r'budget', views.BudgetViewSet)


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', RedirectView.as_view(url='/dashboard/')),
    path('income/', views.IncomeView.as_view(), name='income'),
    path('income/edit/<int:pk>', views.EditIncomeView.as_view(), name='edit_income'),
    path('expense/', views.ExpenseView.as_view(), name='expense'),
    path('expense/edit/<int:pk>', views.EditExpenseView.as_view(), name='edit_expense'),
    path('budget/', views.BudgetView.as_view(), name='budget'),
    path('budget/edit/<int:pk>', views.EditBudgetView.as_view(), name='edit_budget'),
    path('api/', include(router.urls)),
]
