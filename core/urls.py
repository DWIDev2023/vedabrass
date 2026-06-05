from django.urls import path, include
from . import views

urlpatterns = [
    path('errors/400', views.WebError400, name="WebError400"),
    path('errors/403', views.WebError403, name="WebError403"),
    path('errors/404', views.WebError404, name="WebError404"),
    path('errors/405', views.WebError405, name="WebError405"),
    path('errors/408', views.WebError408, name="WebError408"),
    path('errors/419', views.WebError419, name="WebError419"),
    path('errors/500', views.WebError500, name="WebError500"),
    path('errors/503', views.WebError503, name="WebError503"),

    path('admin/errors/400', views.AdminError400, name="AdminError400"),
    path('admin/errors/403', views.AdminError403, name="AdminError403"),
    path('admin/errors/404', views.AdminError404, name="AdminError404"),
    path('admin/errors/405', views.AdminError405, name="AdminError405"),
    path('admin/errors/408', views.AdminError408, name="AdminError408"),
    path('admin/errors/419', views.AdminError419, name="AdminError419"),
    path('admin/errors/500', views.AdminError500, name="AdminError500"),
    path('admin/errors/503', views.AdminError503, name="AdminError503"),

    path('', views.Welcome, name="Welcome"),
    path('who-we-are', views.WhoWeAre, name="WhoWeAre"),

    path('categories', views.Categories, name="Categories"),
    path('subcategories/<str:slug>', views.Subcategory, name="Subcategory"),
    path('collections/<str:slug>', views.Collections, name="Collections"),

    path('search-products', views.SearchProducts, name="SearchProducts"),
    path('products', views.Products, name="Products"),
    path('category-products/<str:slug>', views.ProductsByCategory, name="ProductsByCategory"),
    path('subcategory-products/<str:slug>', views.ProductsBySubcategory, name="ProductsBySubcategory"),
    path('collection-products/<str:slug>', views.ProductsByCollection, name="ProductsByCollection"),
    path('products-premium-collection', views.ProductsPremiumCollection, name="ProductsPremiumCollection"),
    path('product-details/<str:slug>', views.ProductDetails, name="ProductDetails"),

    path('cart', views.Carts, name="Carts"),
    path('add-to-cart/<str:slug>', views.AddToCart, name="AddToCart"),
    path('update-cart/<str:code>', views.UpdateCart, name="UpdateCart"),
    path('remove-from-cart/<str:code>', views.RemoveFromCart, name="RemoveFromCart"),
    path('check-out', views.CheckOut, name="CheckOut"),
    path('place-order', views.PlaceOrder, name="PlaceOrder"),
    path('track-order/<str:code>', views.TrackOrder, name="TrackOrder"),

    path('thank-you/<str:code>', views.ThankYou, name="ThankYou"),

    path('contact-us', views.Contact, name="Contact"),
    path('shipping-policy', views.ShippingPolicy, name="ShippingPolicy"),
    path('return-policy', views.ReturnPolicy, name="ReturnPolicy"),
    path('privacy-policy', views.PrivayPolicy, name="PrivayPolicy"),
    path('terms-and-conditions', views.TermsUse, name="TermsUse"),

    path('blogs', views.Blogs, name="Blogs"),
    path('blog/<str:slug>', views.BlogDetails, name="BlogDetails"),

    path('subscribe', views.Subscribe, name="Subscribe"),
    path('submit-review', views.SubmitReview, name="SubmitReview"),

    path('sign-up', views.SignUp, name="SignUp"),
    path('sign-in', views.SignIn, name="SignIn"),

    path('master/dashboard/<str:code>', views.AdminDashboard, name="AdminDashboard"),

    path('master/all-orders/<str:code>', views.AdminOrders, name="AdminOrders"),
    path('master/view-order/<str:code>/<str:cid>', views.AdminViewOrder, name="AdminViewOrder"),
    path('master/edit-order/<str:code>', views.AdminEditOrder, name="AdminEditOrder"),
    path('master/delete-order/<str:code>', views.AdminDeleteOrder, name="AdminDeleteOrder"),

    path('master/all-customers/<str:code>', views.AdminCustomers, name="AdminCustomers"),
    path('master/view-customer-details/<str:code>/<str:ccode>', views.AdminViewCustomer, name="AdminViewCustomer"),
    path('master/edit-customer-details/<str:code>', views.AdminEditCustomer, name="AdminEditCustomer"),
    path('master/edit-customer-address/<str:code>', views.AdminEditCustomerAddress, name="AdminEditCustomerAddress"),
    path('master/delete-customer/<str:code>', views.AdminDeleteCustomer, name="AdminDeleteCustomer"),

    path('master/all-product-reviews/<str:code>', views.AdminProductReviews, name="AdminProductReviews"),
    path('master/edit-product-review/<str:code>/<str:rcode>', views.AdminEditProductReview, name="AdminEditProductReview"),
    path('master/delete-product-review/<str:code>', views.AdminDeleteProductReview, name="AdminDeleteProductReview"),

    path('master/all-contacts/<str:code>', views.AdminContacts, name="AdminContacts"),
    path('master/delete-contact/<str:code>', views.AdminDeleteContact, name="AdminDeleteContact"),

    path('master/all-newsletter-subscribers/<str:code>', views.AdminNewsletterSubscribers, name="AdminNewsletterSubscribers"),
    path('master/delete-newsletter-subscribers/<str:code>', views.AdminDeleteNewsletterSubscribers, name="AdminDeleteNewsletterSubscribers"),

    path('master/all-vendors/<str:code>', views.AdminVendors, name="AdminVendors"),
    path('master/add-new-vendor/<str:code>', views.AdminNewVendor, name="AdminNewVendor"),
    path('master/edit-vendor/<str:code>', views.AdminEditVendor, name="AdminEditVendor"),
    path('master/delete-vendor/<str:code>', views.AdminDeleteVendor, name="AdminDeleteVendor"),

    path('master/all-categories/<str:code>', views.AdminCategories, name="AdminCategories"),
    path('master/add-new-category/<str:code>', views.AdminNewCategory, name="AdminNewCategory"),
    path('master/edit-category/<str:code>', views.AdminEditCategory, name="AdminEditCategory"),
    path('master/delete-category/<str:code>', views.AdminDeleteCategory, name="AdminDeleteCategory"),

    path('master/fetch-subcategories', views.AdminFetchSubcategory, name="AdminFetchSubcategory"),
    path('master/view-subcategories/<str:code>/<str:slug>', views.AdminViewSubcategory, name="AdminViewSubcategory"),
    path('master/add-new-subcategory/<str:code>/<str:slug>', views.AdminNewSubcategory, name="AdminNewSubcategory"),
    path('master/edit-subcategory/<str:code>', views.AdminEditSubcategory, name="AdminEditSubcategory"),
    path('master/delete-subcategory/<str:code>', views.AdminDeleteSubcategory, name="AdminDeleteSubcategory"),

    path('master/fetch-collections', views.AdminFetchCollection, name="AdminFetchCollection"),
    path('master/view-collections/<str:code>/<str:slug1>/<str:slug2>', views.AdminViewCollection, name="AdminViewCollection"),
    path('master/add-new-collection/<str:code>/<str:slug1>/<str:slug2>', views.AdminNewCollection, name="AdminNewCollection"),
    path('master/edit-collection/<str:code>', views.AdminEditCollection, name="AdminEditCollection"),
    path('master/add-products-in-collection/<str:code>', views.AdminAddProductInCollection, name="AdminAddProductInCollection"),
    path('master/delete-collection/<str:code>', views.AdminDeleteCollection, name="AdminDeleteCollection"),

    path('master/all-products/<str:code>', views.AdminProducts, name="AdminProducts"),
    path('master/add-new-product/<str:code>', views.AdminAddProduct, name="AdminAddProduct"),
    path('master/edit-product/<str:code>', views.AdminEditProduct, name="AdminEditProduct"),
    path('master/delete-product/<str:code>', views.AdminDeleteProduct, name="AdminDeleteProduct"),

    path('master/all-blog-categories/<str:code>', views.AdminBlogCategories, name="AdminBlogCategories"),
    path("add-blog-category/<str:code>", views.AdminNewBlogCategory, name="AdminNewBlogCategory"),
    path("edit-blog-category/<str:code>/", views.AdminEditBlogCategory, name="AdminEditBlogCategory"),
    path("delete-blog-category/<str:code>/", views.AdminDeleteBlogCategory, name="AdminDeleteBlogCategory"),

    path('master/all-blogs/<str:code>', views.AdminBlogs, name="AdminBlogs"),
    path('master/add-new-blog/<str:code>', views.AdminAddNewBlog, name="AdminAddNewBlog"),
    path("master/edit-blog/<str:code>/<str:slug>", views.AdminEditBlog, name="AdminEditBlog"),
    path("master/delete-blog/<str:code>/", views.AdminDeleteBlog, name="AdminDeleteBlog"),

    path('master/account-settingss/<str:code>', views.AdminAccSettings, name="AdminAccSettings"),

    path('sign-out', views.SignOut, name="SignOut"),
]