from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db.models import Q, UniqueConstraint
from django.urls import reverse
from uuid import uuid4
from datetime import datetime, timedelta
from django.utils.text import slugify
import random, string, os, secrets

def code_generator():
    key = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=36))
    # if BlogCategory.objects.filter(unique_code=key).exists():
    #     key = code_generator()
    # elif Blog.objects.filter(unique_code=key).exists():
    #     key = code_generator()

    return key

def category_image_rename(instance, filename):
    upload_to = 'categories'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

def collection_image_rename(instance, filename):
    upload_to = 'collections'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

def product_image_rename(instance, filename):
    upload_to = 'products'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

def review_image_rename(instance, filename):
    upload_to = 'reviews'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

def blog_image_rename(instance, filename):
    upload_to = 'blogs'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Otp(TimeStampedModel):
    email = models.EmailField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    otp = models.CharField(max_length=255, default=000000)
    purpose = models.CharField(max_length=50, default="signup")
    unique_code = models.CharField(max_length=255, default=code_generator, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    expires_at = models.DateTimeField(default=datetime.now() + timedelta(hours=24))

    def is_expired(self):
        return datetime.now() > self.expires_at
    
class Country(TimeStampedModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    capital = models.CharField(max_length=255, null=True, blank=True)
    flag = models.CharField(max_length=255, null=True, blank=True)
    alpha2_code = models.CharField(max_length=255, null=True, blank=True)
    alpha3_code = models.CharField(max_length=255, null=True, blank=True)
    numeric_code = models.CharField(max_length=255, null=True, blank=True)
    currency_code = models.CharField(max_length=255, null=True, blank=True)
    currency_name = models.CharField(max_length=255, null=True, blank=True)
    currency_symbol = models.CharField(max_length=255, null=True, blank=True)
    currency_exchange_rate_to_base = models.CharField(max_length=12, null=True, blank=True)

class CustomUserManager(BaseUserManager):
    def create(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('Account must have an email address'))
        
        email = self.normalize_email(email)

        user = self.model(
            email = email,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user
    
    def create_staffuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_manager", False)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_online", False)
        return self.create(email=email, password=password, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_manager", False)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_online", True)
        return self.create(email=email, password=password, **extra_fields)
    
class User(AbstractBaseUser, TimeStampedModel):
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    mobile = models.CharField(max_length=255, unique=True, null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_manager = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    otp_enabled = models.BooleanField(default=False)
    password_reset_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    role = models.CharField(max_length=255, default='')

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

class UserVerification(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mobile_verified_at = models.DateTimeField(null=True, blank=True)

class Vendor(TimeStampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=255, null=True, blank=True)
    city_code = models.CharField(max_length=255, null=True, blank=True)
    vendor_code = models.CharField(max_length=255, null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

class Tags(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    slug = models.SlugField(unique=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=category_image_rename, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse(
            "ProductsByCategory",
            kwargs={
                "slug": self.slug
            }
        )

class Collection(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='collections')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    scode = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to=collection_image_rename, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse(
            "ProductsByCollection",
            kwargs={
                "slug": self.slug
            }
        )
    
class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, related_name="products")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tags, blank=True, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    sku = models.CharField(max_length=100, null=True, blank=True)
    product_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse(
            "ProductDetails",
            kwargs={
                "slug": self.slug
            }
        )
    
    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
        ]
        ordering = ['-created_at']
    
class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='images')
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    image = models.ImageField(upload_to=product_image_rename, unique=True, null=True, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.product.name

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='attributes')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

class ProductInventory(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, null=True, related_name='inventory')
    quantity = models.IntegerField(default=5)
    low_stock_threshold = models.IntegerField(default=5)

class ProductBundle(TimeStampedModel):
    products = models.ManyToManyField(Product, related_name="bundles")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    short_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    bundle_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discounted_bundle_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bundle_type = models.CharField(
        max_length=50,
        choices=[
            ("pooja", "Pooja"),
            ("festival", "Festival"),
            ("gift", "Gift"),
            ("decor", "Decor"),
            ("kitchen", "Kitchen"),
            ("premium", "Premium"),
        ],
        default="pooja",
    )
    priority = models.PositiveSmallIntegerField(default=0)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse(
            "CuratedBundleDetails",
            kwargs={
                "slug": self.slug
            }
        )

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']

class GiftingCollectionProduct(TimeStampedModel):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="gifting_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gifting_collections")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("collection", "product")
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.collection.name} - {self.product.name}"

class Customer(TimeStampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile = models.CharField(max_length=20)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    gst_number = models.CharField(max_length=50, null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    customer_type = models.CharField(max_length=255, null=True, blank=True, default='Potential')

class CustomerAddress(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, related_name="addresses")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255, default="India")
    postal_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=20, default="Billing")
    is_default = models.BooleanField(default=False)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

class Cart(TimeStampedModel):
    session_key = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="carts")
    is_completed = models.BooleanField(default=False)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.unique_code
    
class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    class Meta:
        unique_together = ("cart", "product")

class Review(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to=review_image_rename, unique=True, null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    featured_order = models.PositiveIntegerField(default=0)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    
class Order(TimeStampedModel):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    )
    PAYMENT_STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    )
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="orders")
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.ForeignKey(CustomerAddress, on_delete=models.SET_NULL, null=True, related_name="billing_orders")
    shipping_address = models.ForeignKey(CustomerAddress, on_delete=models.SET_NULL, null=True, related_name="shipping_orders")
    order_id = models.CharField(max_length=255, unique=True, editable=False, null=True, blank=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_deleted = models.BooleanField(default=False)

    payu_txnid = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    payment_mode = models.CharField(max_length=100, null=True, blank=True)
    payu_mihpayid = models.CharField(max_length=255, null=True, blank=True)
    payment_response = models.JSONField(null=True, blank=True)

    shiprocket_order_id = models.CharField(max_length=255, null=True, blank=True)
    shiprocket_shipment_id = models.CharField(max_length=255, null=True, blank=True)
    shipment_status = models.CharField(max_length=100, null=True, blank=True)
    shiprocket_awb_code = models.CharField(max_length=255, null=True, blank=True)
    shiprocket_courier_name = models.CharField(max_length=255, null=True, blank=True)
    shiprocket_label_url = models.URLField(null=True, blank=True)
    shiprocket_invoice_url = models.URLField(null=True, blank=True)
    tracking_url = models.URLField(null=True, blank=True)
    shiprocket_response = models.JSONField(null=True, blank=True)

    payment_reminder_sent = models.BooleanField(default=False)
    payment_reminder_sent_at = models.DateTimeField(null=True, blank=True)

    invoice_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    invoice_email_sent = models.BooleanField(default=False)
    invoice_email_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.order_id or self.unique_code
    
    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["customer"]),
        ]
    
class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class ContactInquiry(TimeStampedModel):
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_contacted = models.BooleanField(default=False)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.name
    
class Subscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.email
    
class BlogCategory(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse(
            "CategoryBlogs",
            kwargs={
                "slug": self.slug
            }
        )

class Blog(TimeStampedModel):
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name="blogs")
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to=blog_image_rename, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to=blog_image_rename, unique=True, null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField()
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class FAQ(TimeStampedModel):
    CATEGORY_CHOICES = (
        ("General", "General"),
        ("Product", "Product"),
        ("Shipping", "Shipping"),
        ("Payment", "Payment"),
        ("Invoice", "Invoice"),
        ("Return", "Return"),
        ("Care", "Care"),
        ("Gifting", "Gifting"),
        ("Blog", "Blog"),
    )

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default="General")
    page = models.CharField(max_length=255, null=True, blank=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    keywords = models.TextField(null=True, blank=True, help_text="Comma separated keywords for chatbot search")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="faqs")
    bundle = models.ForeignKey(ProductBundle, on_delete=models.SET_NULL, null=True, blank=True, related_name="faqs")
    blog = models.ForeignKey(Blog, on_delete=models.SET_NULL, null=True, blank=True, related_name="faqs")
    is_active = models.BooleanField(default=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.question
    
class NotificationLog(TimeStampedModel):
    CHANNEL_CHOICES = (
        ("Email", "Email"),
        ("WhatsApp", "WhatsApp"),
        ("SMS", "SMS"),
        ("Offline", "Offline"),
    )
    STATUS_CHOICES = (
        ("Success", "Success"),
        ("Failed", "Failed"),
        ("Pending", "Pending"),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notification_logs")
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES)
    event = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    recipient = models.CharField(max_length=255, null=True, blank=True)
    response = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["channel"]),
            models.Index(fields=["event"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
    
class ChatbotKeyword(models.Model):
    keyword = models.CharField(max_length=150, db_index=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, null=True, blank=True, on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.keyword
    
    class Meta:
        unique_together = ("keyword", "category", "collection", "tag")
        ordering = ["-priority", "keyword"]

class ChatSession(TimeStampedModel):
    session_key = models.CharField(max_length=255, db_index=True)
    current_state = models.CharField(max_length=100, default="greeting")
    context = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.session_key

class ChatMessage(TimeStampedModel):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=20)  # user / bot
    message = models.TextField()
    intent = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:40]}"

class SupportTicket(TimeStampedModel):
    STATUS_CHOICES = (
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Closed", "Closed"),
    )
    SOURCE_CHOICES = (
        ("Chatbot", "Chatbot"),
        ("Manual", "Manual"),
        ("WhatsApp", "WhatsApp"),
        ("Email", "Email"),
        ("Phone", "Phone"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(ChatSession, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="Manual")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Open")
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.subject

class NewsEvent(TimeStampedModel):
    PLATFORM_CHOICES = (
        ("instagram", "Instagram"),
        ("youtube", "YouTube"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("twitter", "Twitter"),
        ("other", "Other"),
    )
    MEDIA_TYPE = (
        ("image", "Image"),
        ("video", "Video"),
    )

    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE)

    media_url = models.URLField()
    external_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # NEW: product / bundle tagging
    product = models.ManyToManyField("Product", blank=True)
    bundle = models.ManyToManyField("ProductBundle", blank=True)

    # engagement tracking
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
class ChatbotSearchLog(TimeStampedModel):
    RESULT_TYPES = (
        ("FAQ", "FAQ"),
        ("PRODUCT", "PRODUCT"),
        ("BUNDLE", "BUNDLE"),
        ("SUPPORT", "SUPPORT"),
        ("EMPTY", "EMPTY"),
        ("TRACK_ORDER", "TRACK_ORDER"),
        ("INVOICE", "INVOICE"),
    )

    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL,)
    session = models.ForeignKey(ChatSession, null=True, blank=True, on_delete=models.SET_NULL)
    query = models.CharField(max_length=500, db_index=True)
    matched_faq = models.ForeignKey(FAQ, null=True, blank=True, on_delete=models.SET_NULL)
    matched_bundle = models.ForeignKey(ProductBundle, null=True, blank=True, on_delete=models.SET_NULL)
    matched_products = models.ManyToManyField(Product, blank=True, related_name="chatbot_logs")
    support_ticket = models.ForeignKey(SupportTicket, null=True, blank=True, on_delete=models.SET_NULL)
    selected_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="clicked_chatbot_logs")
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES, db_index=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)

    def __str__(self):
        return self.query

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["result_type"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["session"]),
        ]

