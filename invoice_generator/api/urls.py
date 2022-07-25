from django.urls import path
from .views import *

urlpatterns = [
    path('items/<int:id>/', get_item),
    path('items/create/', add_item),
    path('items/update/<str:name>/', update_item),
    path('items/delete/<str:name>/', delete_item),
    path('items/all/', get_all_items),

    path('orders/create/', create_order),
    path('orders/update/', update_order),
    path('orders/items/', get_order_items),
    path('orders/invoice/', get_invoice_pdf),

    path('customers/create/', create_customer),
    path('customers/login/', login_customer),
    path('customers/logout/', logout_customer),
]