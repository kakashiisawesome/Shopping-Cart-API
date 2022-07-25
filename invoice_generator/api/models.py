from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default='')
    price_per_unit = models.DecimalField(decimal_places=2, max_digits=9, default=0.0)
    available_quantity = models.IntegerField(default=0)
    # TODO add is_active instead of deleting

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    active = models.BooleanField(default=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, related_name='orders', null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', null=True)
    item_name = models.CharField(max_length=200, null=True)
    quantity = models.IntegerField(default=0)