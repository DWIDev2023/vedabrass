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
from uuid import uuid4
from datetime import datetime, timedelta
from django.utils.text import slugify
import random, string, os, secrets

def code_generator():
    key = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=36))
    # if Otp.objects.filter(unique_code=key).exists():
    #     key = code_generator()
    # elif User.objects.filter(unique_code=key).exists():
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
    image = models.ImageField(upload_to=category_image_rename, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Collection(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='collections')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    scode = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to=collection_image_rename, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)
    
class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, related_name="products")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tags, blank=True, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    sku = models.CharField(max_length=100, null=True, blank=True)
    product_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    unique_code = models.CharField(max_length=255, unique=True, default=code_generator, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
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

    def __str__(self):
        return self.unique_code
    
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Blog(TimeStampedModel):
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name="blogs")
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    meta_title = models.TextField(null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=blog_image_rename, unique=True, null=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField()
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
