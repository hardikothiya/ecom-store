from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, connection
from django.db.models import Q, F, Value, Func, Min, ExpressionWrapper, DecimalField
from django.db.models.aggregates import Count, Min, Max, Sum, Avg
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail, mail_admins, mail_managers, send_mass_mail, BadHeaderError, EmailMessage
from tags.models import TaggedItem
from .tasks import notify_customer
from store.models import Product, OrderItem, Order, Customer, Collection
import requests
from rest_framework.views import APIView
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


# Create your views here.

#@transaction.atomic() # Wraps the whole function in transaction
def say_hello(request):
    # Retrival
    product = Product.objects.get(pk=1)  # Return Object Instance
    product = Product.objects.filter(pk=1).first()
    product = Product.objects.filter(pk=0).exists()  # Bool

    query_set = Product.objects.all()  # Returns querysets

    # Filtering Data
    query_set = Product.objects.filter(unit_price=20)
    query_set = Product.objects.filter(unit_price__gte=20)
    query_set = Product.objects.filter(unit_price__range=(20, 50))

    # Fileter across relationship
    query_set = Product.objects.filter(collection__id__range=(1, 3))

    query_set = Product.objects.filter(collection__id__in=[1, 2])
    query_set = Product.objects.filter(
        title__icontains='coffee')  # Incase sensitive
    query_set = Product.objects.filter(last_update__year=2020)
    query_set = Product.objects.filter(description__isnull=True)

    # complex lookup (Q object)
    # And Condition
    query_set = Product.objects.filter(inventory__lt=10, unit_price__gt=10)
    query_set = Product.objects.filter(
        inventory__lt=10).filter(unit_price__gt=10)

    # OR Conditionn
    query_set = Product.objects.filter(
        Q(inventory__lt=10) | Q(unit_price__gt=10))
    query_set = Product.objects.filter(
        Q(inventory__lt=10) & ~Q(unit_price__gt=10))  # ~ Operator

    ###################################################################

    # Referencing Fields (F Object)
    # inventory = price
    query_set = Product.objects.filter(inventory=F('unit_price'))
    query_set = Product.objects.filter(inventory=F('collection__id'))

    # Sorting Data
    query_set = Product.objects.order_by("unit_price", "-title")
    product = Product.objects.order_by("unit_price", "-title").reverse()[0]
    # Get First Object After Sorting Asc
    product = Product.objects.earliest("unit_price")
    # Get First Object After Sorting Desc
    product = Product.objects.latest("unit_price")
    query_set = Product.objects.filter(
        unit_price__gte=10).order_by("unit_price", "-title")

    # Limiting Results
    query_set = Product.objects.all()[5:10]  # Limit 5 Offset 5

    ###################################################################

    # Subset of fields
    # returns list of dict
    query_set = Product.objects.values("id", "title")[5:10]
    query_set = Product.objects.values(
        "id", "title", "collection__title")  # Related Fields
    # returns list of Tuple
    query_set = Product.objects.values_list("id", "title")[5:10]

    # Deferring Fields (Returns instances)
    # If we access fields apart from these It will create Extra queries for that field
    query_set = Product.objects.only("id", "title")[5:10]
    # All fields except Description
    query_set = Product.objects.defer("description")[5:10]

    ###################################################################

    # Join Operation / Subquery
    query_set = Product.objects.filter(id__in=OrderItem.objects.values(
        'product_id').distinct()).order_by('title').values('title')  # Distinct : Unique values

    ###################################################################

    # Selecting Related Objects
    # select related (1)
    query_set = Product.objects.select_related('collection').all()
    # prefetch related(n)
    query_set = Product.objects.prefetch_related('promotions').all()
    query_set = Product.objects.prefetch_related(
        'promotions').select_related('collection').all()[0:7]
    print(list(query_set))

    query_set = Order.objects.select_related('customer').prefetch_related(
        'orderitem_set__product').order_by('-placed_at')[0:5]
    print(list(query_set))
    for order in query_set:
        print(order.customer.first_name)
        for order_item in order.orderitem_set.all():
            print(order_item.product.title)

    ###################################################################

    # Aggregating Objects

    result = Product.objects.aggregate(count=Count("id"),
                                       min_price=Min('unit_price'),
                                       avg_price=Avg('unit_price')
                                       )  # Keys are dynamic for result
    result = Product.objects.filter(collection__id=3).aggregate(count=Count("id"),
                                                                min_price=Min(
                                                                    'unit_price'),
                                                                avg_price=Avg(
                                                                    'unit_price')
                                                                )

    #################################  Annotate ##############################
    # Add new filed in runtime

    # Can't pass bool accepts expressions
    query_set = Customer.objects.annotate(is_new=Value(True))
    query_set = Customer.objects.annotate(new_id=F('id') + 1000)

    ################################# Database Function ##############################
    query_set = Customer.objects.annotate(full_name=Func(
        F('first_name'), Value(' '), F('last_name'), function='CONCAT'))  # Can use custom created Db Functions

    query_set = Customer.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name'))

    ################################# Grouping Data ##############################

    # can't user order_set revrse relation for count
    query_set = Customer.objects.annotate(orders_count=Count('order'))

    ################################# Expression wrapper ##############################

    # Set the output filed (decimal * Float)
    discounted_price = ExpressionWrapper(F('unit_price') * 0.8, output_field=DecimalField())

    query_set = Product.objects.annotate(discount_price=discounted_price)

    ################################# Generic Relationships ##############################

    content_type = ContentType.objects.get_for_model(Product)
    query_set = TaggedItem.objects.select_related('tag').filter(
        content_type=content_type,
        object_id__in=[1, 4]
    )

    ################################# Custom Managers ##############################

    query_set = TaggedItem.objects.get_tags_for(Product, 1)  # custom manager function
    query_set = TaggedItem.objects.all()

    ################################# Queryset Cache ##############################

    print(list(query_set))  # Reading all Records First
    print(list(query_set[0:10]))  # Read Data from cache of above queryset

    ################################# Create Object ##############################

    collection = Collection()
    collection.title = 'Video Games'
    collection.featured_product = Product(pk=1)  # featured_product_id =1
    # collection.save()
    # print(collection.id)

    #OR

    # collection = Collection.objects.create(
    #     title='Ott Media',
    #     featured_product_id=1
    # )
    # print(collection.id)

    ################################# Update Object ##############################

    # collection = Collection(pk=17) # Update Only given fields and set other fields = ''

    # collection = Collection.objects.get(pk=17) # Get Loads instance data in memory First
    # collection.title = 'Audio Books'
    # collection.featured_product = None
    # collection.save()

    #Or
    Collection.objects.filter(pk=17).update(featured_product_id=1)

    ################################# Delete Object ##############################
    collection = Collection(pk=9)
    collection.delete()

    Collection.objects.filter(id__gt=10).delete()

    ################################# Transactions ##############################

    with transaction.atomic():

        order = Order()
        order.customer_id = 1
        order.save()

        item = OrderItem()
        item.order = order
        item.product_id = 2
        item.unit_price = 10
        item.quantity = 1
        item.save()

    ################################# RAW SQL Queries ##############################

    # raw_query_set = Product.objects.raw("SELECT * FROM store_product")

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM store_product")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

        # call_sp = cursor.callproc('get_customers', [1,2,'a']) # Call store procedure with arguments

    return render(request, 'hello.html', {"name": 'Hardk', 'products': list(query_set), "result": result})


def mails(request):
    # BadHeaderError : security measure for header modifications
    try:
        # send_mail('Subject', 'Body', 'mymail@mail.com', ['receiver1@gmail.com'])
        mail_admins('Subject', 'message', html_message='message')  #

        # EmailMessage
        message = EmailMessage('Subject', 'Body', 'mymail@mail.com', ['receiver1@gmail.com'])
        message.attach_file('playground/static/images/download.png')
        message.send()

    except BadHeaderError:
        pass
    return HttpResponse('ok')


def send_marketing_mails(request):
    notify_customer.delay("Hello")
    return HttpResponse("OK")


def cache_test(request):
    if cache.get('httpbin_result') is None:
        result = requests.get('https://httpbin.org/delay/2')
        httpbin_result = result.json()
        cache.set('httpbin_result', httpbin_result, 10 * 60)
    return HttpResponse(cache.get('httpbin_result').__str__())


@cache_page(5 * 20) # For Function Based Views Only
def cache_test2(request):
    result = requests.get('https://httpbin.org/delay/2')
    httpbin_result = result.json()
    return HttpResponse(httpbin_result)

class HelloCache(APIView):

    @method_decorator(cache_page(5 * 20) ) # For Function Based Views Only
    def get(self, request):
        result = requests.get('https://httpbin.org/delay/2')
        httpbin_result = result.json()
        return HttpResponse(httpbin_result)

