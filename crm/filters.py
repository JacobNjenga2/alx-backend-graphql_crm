import django_filters
from django.db import models
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', help_text="Filter by name (case-insensitive partial match)")
    email = django_filters.CharFilter(lookup_expr='icontains', help_text="Filter by email (case-insensitive partial match)")
    created_at = django_filters.DateTimeFilter(help_text="Filter by exact creation date")
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text="Filter by creation date (greater than or equal)")
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text="Filter by creation date (less than or equal)")
    
    # Custom filter for phone number pattern
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern', help_text="Filter by phone number pattern (e.g., starts with +1)")
    
    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter to match customers with specific phone number patterns"""
        if value:
            return queryset.filter(phone__icontains=value)
        return queryset

    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'phone': ['exact', 'icontains'],
            'created_at': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
        }


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', help_text="Filter by name (case-insensitive partial match)")
    price = django_filters.NumberFilter(help_text="Filter by exact price")
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte', help_text="Filter by price (greater than or equal)")
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte', help_text="Filter by price (less than or equal)")
    stock = django_filters.NumberFilter(help_text="Filter by exact stock")
    stock__gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte', help_text="Filter by stock (greater than or equal)")
    stock__lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte', help_text="Filter by stock (less than or equal)")
    
    # Custom filter for low stock
    low_stock = django_filters.BooleanFilter(method='filter_low_stock', help_text="Filter products with low stock (< 10)")
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock (stock < 10)"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'stock': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'created_at': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
        }


class OrderFilter(django_filters.FilterSet):
    total_amount = django_filters.NumberFilter(help_text="Filter by exact total amount")
    total_amount__gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte', help_text="Filter by total amount (greater than or equal)")
    total_amount__lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte', help_text="Filter by total amount (less than or equal)")
    
    order_date = django_filters.DateTimeFilter(help_text="Filter by exact order date")
    order_date__gte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='gte', help_text="Filter by order date (greater than or equal)")
    order_date__lte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='lte', help_text="Filter by order date (less than or equal)")
    
    # Related field filters
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains', help_text="Filter by customer name (case-insensitive partial match)")
    customer_email = django_filters.CharFilter(field_name='customer__email', lookup_expr='icontains', help_text="Filter by customer email (case-insensitive partial match)")
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains', help_text="Filter by product name (case-insensitive partial match)")
    
    # Custom filter for specific product ID
    product_id = django_filters.NumberFilter(method='filter_by_product_id', help_text="Filter orders that include a specific product ID")
    
    def filter_by_product_id(self, queryset, name, value):
        """Filter orders that include a specific product ID"""
        if value:
            return queryset.filter(products__id=value).distinct()
        return queryset

    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'order_date': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
            'customer': ['exact'],
            'created_at': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
        }
