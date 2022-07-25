from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import *
from .serializers import ItemSerializer, CustomerSerializer, OrderItemSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import permissions
from rest_framework.permissions import AllowAny
import io
from reportlab.pdfgen import canvas
from django.http import HttpResponse, FileResponse


# Item CRUD views
@api_view(['GET'])
def get_item(request, id):
    if request.method == 'GET':
        check_user_auth(request)
        item = get_object_or_404(Item, id=id)
        serializer = ItemSerializer(item)
        return Response(serializer.data)


@api_view(['POST'])
def add_item(request):
    if request.method == 'POST':
        check_user_auth(request)
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response()
        else:
            return Response(serializer.errors, status=400)


@api_view(['PUT'])
def update_item(request, name):
    if request.method == 'PUT':
        check_user_auth(request)
        item = get_object_or_404(Item, name=name)
        serializer = ItemSerializer(instance=item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=404)


@api_view(['DELETE'])
def delete_item(request, name):
    if request.method == 'DELETE':
        check_user_auth(request)
        item = get_object_or_404(Item, name=name)
        item.delete()
        return Response()


# Returns all items
@api_view(['GET'])
def get_all_items(request):
    if request.method == 'GET':
        check_user_auth(request)
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)


# Get current order items
@api_view(['GET'])
def get_order_items(request):
    if request.method == 'GET':
        check_user_auth(request)
        # Get current active order of the customer
        order = request.user.customer.orders.filter(active=True).first()
        if order is None:
            return Response([])

        order_items = order.order_items.all()
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def create_order(request):
    if request.method == 'POST':
        check_user_auth(request)
        # Return if user already has an active order
        if request.user.customer.orders.filter(active=True).exists():
            return Response('Please generate invoice of current pending order first!', status=400)

        order_items = request.data['order_items']
        # Create order with Customer set
        order = Order(customer=request.user.customer)
        order.save()
        # Create Orderitems and assign order to each Orderitem
        for item in order_items:
            print(item)
            # Check if item ordered exists and quantity is sufficient
            try:
                stock_item = Item.objects.get(name=item['item_name'])
            except Item.DoesNotExist:
                order.delete()
                return Response(item['item_name'] + ' does not exist', status=400)

            if stock_item.available_quantity < item['quantity']:
                order.delete()
                return Response(item['item_name'] + ' is out of stock', status=400)

            # OrderItem Created
            orderItem = OrderItem(order=order, item_name=item['item_name'], quantity=item['quantity'])
            orderItem.save()

        return Response('Order saved')


@api_view(['PUT'])
def update_order(request):
    if request.method == 'PUT':
        order = request.user.customer.orders.filter(active=True).first()
        if order is None:
            return Response('No active order found', status=400)

        order_items = request.data['order_items']
        new_items = []
        for item in order_items:
            # Check if item ordered exists and quantity is sufficient
            try:
                stock_item = Item.objects.get(name=item['item_name'])
            except Item.DoesNotExist:
                return Response(item['item_name'] + ' does not exist', status=400)

            if stock_item.available_quantity < item['quantity']:
                return Response(item['item_name'] + ' is out of stock', status=400)

            orderItem = OrderItem(order=order, item_name=item['item_name'], quantity=item['quantity'])
            new_items.append(orderItem)

        # Delete current associated items of the order
        OrderItem.objects.filter(order=order).delete()

        # Add new order items to order
        for item in new_items:
            item.save()

        serializer = OrderItemSerializer(new_items, many=True)
        return Response(serializer.data)


# Generate and send an invoice pdf to the client
@api_view(['GET'])
def get_invoice_pdf(request):
    if request.method == 'GET':
        customer = request.user.customer
        order = customer.orders.filter(active=True).first()
        if order is None:
            return Response('No active order found', status=400)

        order_items = OrderItem.objects.filter(order=order).all()
        item_names = [item.item_name for item in order_items]
        quantities = [item.quantity for item in order_items]

        response = generatePDF(item_names, quantities, customer)
        return response


# Generate invoice pdf
def generatePDF(item_names, quantities, customer):
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    pdf = canvas.Canvas(buffer, bottomup=False)
    x, y = 30, 100

    for (name, quantity) in zip(item_names, quantities):
        pdf.drawString(x, y, name)
        pdf.drawString(x + 100, y, str(quantity))
        y = y + 50

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='invoice.pdf')


# Create Customer view
@api_view(['POST'])
# This view should be accessible by unauthenticated users.
@permission_classes([AllowAny])
def create_customer(request):
    if request.method == 'POST':
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            if User.objects.filter(username=serializer.validated_data['username']).exists():
                return Response('User with that username already exists', status=400)

            # Create User object to associate with the Customer
            user = User.objects.create_user(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
            customer = serializer.save()
            customer.user = user
            customer.save()
            return Response('User created successfully')
        else:
            return Response(serializer.errors, status=400)


# Login Customer view
@api_view(['POST'])
# This view should be accessible by unauthenticated users.
@permission_classes([AllowAny])
def login_customer(request):
    if request.method == 'POST':
        username = request.data['username']
        password = request.data['password']
        if request.user.is_authenticated:
            return Response('User already logged in', status=400)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response('Login success')
        else:
            return Response('Invalid user credentials', status=400)


# Logout Customer view
@api_view(['GET'])
def logout_customer(request):
    if request.method == 'GET':
        check_user_auth(request)
        logout(request)
        return Response('Logged out successfully')


def check_user_auth(request):
    if not request.user.is_authenticated:
        return Response('Unauthenticated user, please login first', status=400)