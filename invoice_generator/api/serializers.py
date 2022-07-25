from rest_framework import serializers
from .models import Item, Customer


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ('name', 'description', 'price_per_unit', 'available_quantity')


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50, write_only=True, trim_whitespace=False)

    def create(self, validated_data):
        return Customer.objects.create(name=validated_data['name'], phone=validated_data['phone'], address=validated_data['address'])

    class Meta:
        model = Customer
        fields = ('password', 'username', 'name', 'phone', 'address')


class OrderItemSerializer(serializers.Serializer):
    item_name = serializers.CharField(max_length=50)
    quantity = serializers.IntegerField()