from rest_framework import serializers
from decimal import Decimal

from .models import Product, Collection, Review, Cart, CartItem


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']
        read_only_fields = ('products_count',)

    # url = serializers.HyperlinkedIdentityField('collection-detail')  # Add Hyperlink
    products_count = serializers.IntegerField(read_only=True)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'inventory', 'description', 'unit_price', 'price_with_tax', 'collection']

    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')

    # price = serializers.DecimalField(max_digits=6, decimal_places=2,
    #                                  source='unit_price')  # Source : Field name in model object

    # Serialize Relationship

    collection = serializers.PrimaryKeyRelatedField(  # Returns Id of collection
        queryset=Collection.objects.all()
    )

    # collection = serializers.StringRelatedField()  # Returns __str__ representation

    # collection = CollectionSerializer()

    # collection = serializers.HyperlinkedRelatedField( # Returns Hyperlink
    #     queryset=Collection.objects.all(),
    #     view_name='collection-detail'
    # )

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)

    # Custom validator
    def validate(self, data):
        if data['inventory'] <= 0:
            raise serializers.ValidationError("Low inventory")
        return data

    # Override default create method
    def create(self, validated_data):
        product = Product(**validated_data)
        product.unit_price = validated_data['unit_price'] * Decimal(1.1)
        product.save()
        return product

    # Override default Update method
    # def update(self, instance, validated_data):
    #     instance.unit_price = validated_data.get("unit_price")
    #     instance.slug = validated_data.get('slug')
    #     instance.save()
    #     return instance


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'description', 'date']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(
            product_id=product_id,
            **validated_data
        )


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    def get_total_price(self, cart_item):
        return cart_item.quantity * cart_item.product.unit_price


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    def get_total_price(self, cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Enter valid product Id")
        return value

    # Base method For Update() and create()
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            # self.instance =  CartItem.objects.create(cart_id=cart_id, product_id=product_id,quantity=quantity)
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['id', 'quantity']
