from django.urls import reverse
from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html, urlencode

from . import models
from .models import ProductImage


#admin.site.register(models.Product, ProductAdmin)
#admin.site.register(models.Product)


class InventoryFilter(admin.SimpleListFilter):
    title = 'Inventory'
    parameter_name = 'inventory'
    
    def lookups(self, request, model_admin):
        return [
            ('<10', 'Low'),
            ('>10', 'Ok')
        ]

    def queryset(self, request, queryset):
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)
        elif self.value() == ">10":
            return queryset.filter(inventory__gte=10)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    readonly_fields = ['thumbnail']

    # Render Image thumbnail for admin
    def thumbnail(self, instance):
        if instance.image.name != '':
            return format_html(f'<image src={instance.image.url} class = "thumbnail" >  ')
        return ''


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):

    # Form Fields Options for adding Product
    # fields = ['title', 'slug']
    # exclude = ['promotions]
    # readonly_fields = ['title']

    autocomplete_fields = ['collection'] # need to define search field in CollectionAdmin
    prepopulated_fields = {
        "slug" : ['title']
    }

    actions = ['clear_inventory']
    list_display = ['title', 'unit_price', 'inventory_status', 'collection_title']
    list_editable = ['unit_price']
    list_per_page = 10
    list_select_related = ['collection']
    list_filter = ['collection', 'last_update', InventoryFilter]
    search_fields = ['title']
    inlines = [ProductImageInline]
    def collection_title(self, product):
        return product.collection.title

    @admin.display(ordering='inventory')
    def inventory_status(self, product):
        """
        Display custom field in Admin Panel
        """

        if product.inventory < 10:
            return "LOW"
        else:
            return "OK"
    @admin.action(description="Clear Inventory")
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        return self.message_user(
            request,
            f"{updated_count} were successfully updated.",
            messages.ERROR
        )

    # To appy css to thumbnail
    class Media:
        css = {
            'all' : ['store/style.css']
        }


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'membership', 'orders_count'] #GET first_name and last_name from Model Methods
    list_editable = ['membership']
    list_per_page = 10
    # ordering = ['user__first_name', 'user__last_name'] # Using Decorator in Customer Model
    search_fields = ['user__first_name__istartswith', 'user__last_name__istartswith']
    autocomplete_fields = ['user']

    def orders_count(self, customer):
        url = reverse("admin:store_order_changelist") + "?" + urlencode({
            "customer__id": str(customer.id)
        })
        return format_html("<a href = {}> {} </a> ", url, customer.orders_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(orders_count=Count('order'))

# class OrderItemInline(admin.StackedInline):

class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['product']
    model = models.OrderItem

    extra = 0
    min_num = 1
    max_num = 10

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment_status', 'customer']
    ordering = ['id']
    list_per_page = 10
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']
    # Links to other page
    @admin.display(ordering='products_count')
    def products_count(self, collection):
        # reverse('admin:app_model_page')
        url = reverse("admin:store_product_changelist") + '?' + urlencode({
            "collection__id": str(collection.id)
        })
        return format_html("<a href = '{}' > {} </a>", url, collection.products_count)

    # Override queryset and annotate with products_count
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('products')
        )


