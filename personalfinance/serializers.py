from rest_framework import serializers
from .models import Expense, Income, Budget

class ExpenseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Expense
        fields = ['amount', 'date', 'description', 'receipt', 'category', 'split', 'divisions','recurring'] 
        
class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ['source', 'amount', 'date', 'description', 'receipt', 'recurring']
        
class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'period']