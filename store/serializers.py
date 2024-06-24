from rest_framework import serializers
from decimal import Decimal

from .models import Product, Collection


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'title', 'url']

    url = serializers.HyperlinkedIdentityField('collection-detail')  # Add Hyperlink

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)


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
        print(data)
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