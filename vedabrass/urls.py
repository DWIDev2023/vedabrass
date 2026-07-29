from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import (
    StaticViewSitemap,
    ProductSitemap,
    CollectionSitemap,
    CategorySitemap,
    CategoryProductsSitemap,
    SubcategoryProductsSitemap,
    CollectionProductsSitemap,
    BlogSitemap,
    BlogCategorySitemap,
    SubcategorySitemap,
    CollectionsLandingSitemap
)

handler400 = "core.views.WebError400"
handler403 = "core.views.WebError403"
handler404 = "core.views.WebError404"
handler500 = "core.views.WebError500"

sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "category_products": CategoryProductsSitemap,
    "subcategory_products": SubcategoryProductsSitemap,
    "collections": CollectionSitemap,
    "collection_products": CollectionProductsSitemap,
    "category": CategorySitemap,
    "subcategory": SubcategorySitemap,
    "collection_landing": CollectionsLandingSitemap,
    "blogs": BlogSitemap,
    "blog_categories": BlogCategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('sonar/', include('django_sonar.urls')),
    path("sitemap.xml", cache_page(60 * 60 * 24)(sitemap), {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap",),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)