from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, DjangoModelPermissions
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Product, Collection, OrderItem, Review, Cart, CartItem, Customer
from .permissions import IsAdminOrReadOnly, FullDjangoModelPermissions, ViewCustomerHistoryPermission
from .serializers import ProductSerializer, CollectionSerializer, ReviewSerializer, CartSerializer, CartItemSerializer, \
    AddCartItemSerializer, UpdateCartItemSerializer, CustomerSerializer
from .filters import ProductFilter
from .pagination import DefaultPagination


class ProductViewSets(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPagination
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']
    permission_classes = [IsAdminOrReadOnly]

    # filterset_fields = ['collection_id', 'unit_price']
    filterset_class = ProductFilter

    # lookup_field = 'id' # Value from URL

    # def get_queryset(self):
    #     queryset = Product.objects.all()
    #     collection_id =  self.request.query_params.get('collection_id', None)
    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response(
                {"Error": "Cannot delete this product as it's associated with order items."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        return super().destroy(request, *args, **kwargs)


class ProductList(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    # Use Methods If we have to perform custom logic
    # def get_queryset(self):
    #     return Product.objects.select_related('collection').all()
    #
    # def get_serializer_class(self):
    #     return ProductSerializer
    #

    # def get(self, request):
    #     queryset = Product.objects.select_related('collection').all()
    #     serializer = ProductSerializer(queryset, many=True, context={'request': request})
    #     return Response(serializer.data)
    #
    # def post(self, request):
    #     serizlizer = ProductSerializer(data=request.data)
    #     serizlizer.is_valid(raise_exception=True)
    #     serizlizer.save()
    #     return Response(serizlizer.data, status=status.HTTP_201_CREATED)


class ProductDetail(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'  # Value from URL

    # def get(self, request, id):
    #     product = get_object_or_404(Product, pk=id)
    #     serializer = ProductSerializer(product)
    #     return Response(serializer.data)
    #
    # def put(self, request, id):
    #     product = get_object_or_404(Product, pk=id)
    #     serializer = ProductSerializer(product, data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)

    # Override delete method
    def delete(self, request, id):
        product = get_object_or_404(Product, pk=id)
        if product.orderitems.count() > 0:
            return Response(
                {"Error": "Cannot delete this product as it's associated with order items."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products'))
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']).count() > 0:
            return Response(
                {"Error": "Cannot delete this collection"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().destroy(request, *args, **kwargs)


class CollectionDetail(RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products'))
    serializer_class = CollectionSerializer

    def delete(self, request, pk):
        collection = get_object_or_404(Collection.objects.annotate(products_count=Count('products')), pk=pk)
        if collection.products.count() > 0:
            return Response(
                {"Error": "Cannot delete this collection"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionList(ListCreateAPIView):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer


class ReviewViewSet(ModelViewSet):
    # queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk']).select_related('product')

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}


# class CustomerViewSet(CreateModelMixin, RetrieveModelMixin,UpdateModelMixin, GenericViewSet):


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    # permission_classes = [DjangoModelPermissions]  # Group Permissions (it allows safe methods by default)
    # permission_classes = [FullDjangoModelPermissions]  # Group/Custom Permissions

    # Override permissions for specific Methods
    # def get_permissions(self):
    #     if self.request.method == "GET":
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    # customers/me/
    @action(detail=False, methods=['GET', "PUT"],
            permission_classes=[IsAuthenticated]  # Override Class permissions for specific actions
            )  # Detail: Detail view
    def me(self, request):
        (customer, created) = Customer.objects.get_or_create(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')
