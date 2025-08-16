from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\+\d{1,3}\d{9,10}|\d{3}-\d{3}-\d{4})$',
                message="Phone must be in format '+1234567890' or '123-456-7890'"
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        ordering = ['name']


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        ordering = ['name']


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name} - ${self.total_amount}"

    def calculate_total(self):
        """Calculate total amount based on associated products"""
        return sum(product.price for product in self.products.all())

    def save(self, *args, **kwargs):
        # For new orders, save with initial total, then update after products are added
        if not self.pk:
            self.total_amount = Decimal('0.00')
        super().save(*args, **kwargs)
    
    def update_total(self):
        """Update the total amount after products are set"""
        self.total_amount = self.calculate_total()
        self.save()

    class Meta:
        ordering = ['-order_date']
