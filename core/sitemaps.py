from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import (
    Product,
    Category,
    Collection,
    BlogCategory,
    Blog
)

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return [
            "Welcome",
            "WhoWeAre",
            "Contact",
            "Categories",
            "CuratedBundles",
            "Products",
            "SearchProducts",
            "ProductsPremiumCollection",
            "Blogs",
            "NewsEvents",
            "Faqs",
            "Reviews",
            "ShippingPolicy",
            "ReturnPolicy",
            "PrivacyPolicy",
            "TermsUse",
        ]

    def location(self, item):
        return reverse(item)
    
class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(
            is_active=True
        ).select_related(
            "category"
        ).only(
            "slug",
            "updated_at",
            "category__slug"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "ProductDetails",
            kwargs={
                "slug": obj.slug
            }
        )
    
class CategorySitemap(Sitemap):
    priority = 0.85
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
    
class SubcategorySitemap(Sitemap):
    priority = 0.75
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=False
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "Subcategory",
            kwargs={
                "slug": obj.slug
            }
        )
    
class CollectionsLandingSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Collection.objects.filter(
            is_active=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "Collections",
            kwargs={
                "slug": obj.slug
            }
        )
    
class CollectionSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Collection.objects.filter(
            is_active=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
    
class CategoryProductsSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "ProductsByCategory",
            kwargs={
                "slug": obj.slug
            }
        )
    
class SubcategoryProductsSitemap(Sitemap):
    priority = 0.75
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=False
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "ProductsBySubcategory",
            kwargs={
                "slug": obj.slug
            }
        )
    
class CollectionProductsSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Collection.objects.filter(
            is_active=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "ProductsByCollection",
            kwargs={
                "slug": obj.slug
            }
        )
    
class BlogCategorySitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return BlogCategory.objects.filter(
            is_active=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
    
class BlogSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return Blog.objects.filter(
            is_active=True
        ).only(
            "slug",
            "updated_at"
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
    
