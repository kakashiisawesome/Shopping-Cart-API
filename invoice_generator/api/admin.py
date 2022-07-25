from django.contrib import admin

# Register your models here.
from .models import Item, Customer, Order, OrderItem

admin.site.register(Item)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)