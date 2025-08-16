import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay, ObjectType, String, List, Field, Mutation, InputObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
import re
from datetime import datetime

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        filter_fields = ['name', 'email', 'phone', 'created_at']
        interfaces = (relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        filter_fields = ['name', 'price', 'stock', 'created_at']
        interfaces = (relay.Node,)


class OrderType(DjangoObjectType):
    products = List(ProductType)
    
    class Meta:
        model = Order
        filter_fields = ['total_amount', 'order_date', 'customer']
        interfaces = (relay.Node,)
    
    def resolve_products(self, info):
        return self.products.all()


# Input Types
class CustomerInput(InputObjectType):
    name = String(required=True)
    email = String(required=True)
    phone = String()


class ProductInput(InputObjectType):
    name = String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()


class OrderInput(InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# Mutation Result Types
class CustomerMutationResult(ObjectType):
    customer = Field(CustomerType)
    message = String()
    success = graphene.Boolean()


class BulkCustomerMutationResult(ObjectType):
    customers = List(CustomerType)
    errors = List(String)
    success = graphene.Boolean()


class ProductMutationResult(ObjectType):
    product = Field(ProductType)
    message = String()
    success = graphene.Boolean()


class OrderMutationResult(ObjectType):
    order = Field(OrderType)
    message = String()
    success = graphene.Boolean()


# Mutations
class CreateCustomer(Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    Output = CustomerMutationResult

    def mutate(self, info, input):
        try:
            # Validate email uniqueness
            if Customer.objects.filter(email=input.email).exists():
                return CustomerMutationResult(
                    customer=None,
                    message="Email already exists",
                    success=False
                )

            # Validate phone format if provided
            if input.phone:
                phone_pattern = r'^(\+\d{1,3}\d{9,10}|\d{3}-\d{3}-\d{4})$'
                if not re.match(phone_pattern, input.phone):
                    return CustomerMutationResult(
                        customer=None,
                        message="Phone must be in format '+1234567890' or '123-456-7890'",
                        success=False
                    )

            # Create customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone
            )

            return CustomerMutationResult(
                customer=customer,
                message="Customer created successfully",
                success=True
            )

        except Exception as e:
            return CustomerMutationResult(
                customer=None,
                message=f"Error creating customer: {str(e)}",
                success=False
            )


class BulkCreateCustomers(Mutation):
    class Arguments:
        input = List(CustomerInput, required=True)

    Output = BulkCustomerMutationResult

    def mutate(self, info, input):
        created_customers = []
        errors = []
        
        try:
            with transaction.atomic():
                for i, customer_data in enumerate(input):
                    try:
                        # Validate email uniqueness
                        if Customer.objects.filter(email=customer_data.email).exists():
                            errors.append(f"Customer {i+1}: Email already exists")
                            continue

                        # Validate phone format if provided
                        if customer_data.phone:
                            phone_pattern = r'^(\+\d{1,3}\d{9,10}|\d{3}-\d{3}-\d{4})$'
                            if not re.match(phone_pattern, customer_data.phone):
                                errors.append(f"Customer {i+1}: Invalid phone format")
                                continue

                        # Create customer
                        customer = Customer.objects.create(
                            name=customer_data.name,
                            email=customer_data.email,
                            phone=customer_data.phone
                        )
                        created_customers.append(customer)

                    except Exception as e:
                        errors.append(f"Customer {i+1}: {str(e)}")

            return BulkCustomerMutationResult(
                customers=created_customers,
                errors=errors,
                success=len(created_customers) > 0
            )

        except Exception as e:
            return BulkCustomerMutationResult(
                customers=[],
                errors=[f"Transaction failed: {str(e)}"],
                success=False
            )


class CreateProduct(Mutation):
    class Arguments:
        input = ProductInput(required=True)

    Output = ProductMutationResult

    def mutate(self, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return ProductMutationResult(
                    product=None,
                    message="Price must be positive",
                    success=False
                )

            # Validate stock is non-negative
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return ProductMutationResult(
                    product=None,
                    message="Stock cannot be negative",
                    success=False
                )

            # Create product
            product = Product.objects.create(
                name=input.name,
                price=Decimal(str(input.price)),
                stock=stock
            )

            return ProductMutationResult(
                product=product,
                message="Product created successfully",
                success=True
            )

        except Exception as e:
            return ProductMutationResult(
                product=None,
                message=f"Error creating product: {str(e)}",
                success=False
            )


class CreateOrder(Mutation):
    class Arguments:
        input = OrderInput(required=True)

    Output = OrderMutationResult

    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return OrderMutationResult(
                    order=None,
                    message="Invalid customer ID",
                    success=False
                )

            # Validate products exist
            if not input.product_ids:
                return OrderMutationResult(
                    order=None,
                    message="At least one product is required",
                    success=False
                )

            products = Product.objects.filter(id__in=input.product_ids)
            if len(products) != len(input.product_ids):
                return OrderMutationResult(
                    order=None,
                    message="One or more invalid product IDs",
                    success=False
                )

            # Calculate total amount
            total_amount = sum(product.price for product in products)

            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    order_date=input.order_date or datetime.now()
                )
                order.products.set(products)
                order.update_total()  # Recalculate total after setting products

            return OrderMutationResult(
                order=order,
                message="Order created successfully",
                success=True
            )

        except Exception as e:
            return OrderMutationResult(
                order=None,
                message=f"Error creating order: {str(e)}",
                success=False
            )


# Query class
class Query(ObjectType):
    # Basic queries
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)
    
    customer = relay.Node.Field(CustomerType)
    product = relay.Node.Field(ProductType)
    order = relay.Node.Field(OrderType)

    # Single item queries
    customer_by_id = Field(CustomerType, id=graphene.ID(required=True))
    product_by_id = Field(ProductType, id=graphene.ID(required=True))
    order_by_id = Field(OrderType, id=graphene.ID(required=True))

    def resolve_customer_by_id(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product_by_id(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_order_by_id(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None


# Mutation class
class Mutation(ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
