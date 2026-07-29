from django.urls import path, include
from . import views

urlpatterns = [
    path('robots.txt', views.RobotsTxt, name="RobotsTxt"),

    path('errors/400', views.WebError400, name="WebError400"),
    path('errors/403', views.WebError403, name="WebError403"),
    path('errors/404', views.WebError404, name="WebError404"),
    path('errors/405', views.WebError405, name="WebError405"),
    path('errors/408', views.WebError408, name="WebError408"),
    path('errors/419', views.WebError419, name="WebError419"),
    path('errors/500', views.WebError500, name="WebError500"),
    path('errors/503', views.WebError503, name="WebError503"),

    path('master/errors/400', views.AdminError400, name="AdminError400"),
    path('master/errors/403', views.AdminError403, name="AdminError403"),
    path('master/errors/404', views.AdminError404, name="AdminError404"),
    path('master/errors/405', views.AdminError405, name="AdminError405"),
    path('master/errors/408', views.AdminError408, name="AdminError408"),
    path('master/errors/419', views.AdminError419, name="AdminError419"),
    path('master/errors/500', views.AdminError500, name="AdminError500"),
    path('master/errors/503', views.AdminError503, name="AdminError503"),

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
    path('add-bundle-to-cart/<str:slug>', views.AddBundleToCart, name="AddBundleToCart"),
    path('remove-from-cart/<str:code>', views.RemoveFromCart, name="RemoveFromCart"),
    path('check-out', views.CheckOut, name="CheckOut"),
    path('place-order', views.PlaceOrder, name="PlaceOrder"),
    path('order/payment/payu/<str:order_id>', views.PayURedirect, name="PayURedirect"),
    path("order/payment/payu/success/", views.PayUSuccess, name="PayUSuccess"),
    path("order/payment/payu/failure/", views.PayUFailure, name="PayUFailure"),
    path("order/payment/failed/<str:code>/", views.PaymentFailed, name="PaymentFailed"),
    path('track-order/<str:code>', views.TrackOrder, name="TrackOrder"),
    path("invoice/<str:invoice_number>/", views.InvoiceView, name="InvoiceView"),

    path('thank-you/<str:code>', views.ThankYou, name="ThankYou"),

    path('contact-us', views.Contact, name="Contact"),
    path('shipping-policy', views.ShippingPolicy, name="ShippingPolicy"),
    path('return-policy', views.ReturnPolicy, name="ReturnPolicy"),
    path('privacy-policy', views.PrivacyPolicy, name="PrivacyPolicy"),
    path('terms-and-conditions', views.TermsUse, name="TermsUse"),

    path('brass-journal', views.Blogs, name="Blogs"),
    path('journal-by-category/<str:slug>', views.CategoryBlogs, name="CategoryBlogs"),
    path('journal/<str:slug>', views.BlogDetails, name="BlogDetails"),

    path('curated-brass-bundles', views.CuratedBundles, name="CuratedBundles"),
    path('curated-brass-bundle/<str:slug>', views.CuratedBundleDetails, name="CuratedBundleDetails"),

    path('news-and-events', views.NewsEvents, name="NewsEvents"),
    path('news-and-events-as-reels', views.NewsReels, name="NewsReels"),
    path('reels-track', views.ReelsTrack, name="ReelsTrack"),
    path('faqs', views.Faqs, name="Faqs"),
    path('reviews', views.Reviews, name="Reviews"),

    path('subscribe', views.Subscribe, name="Subscribe"),
    path('submit-review', views.SubmitReview, name="SubmitReview"),

    path("chatbot/reply/", views.ChatbotReply, name="ChatbotReply"),

    path('sign-up', views.SignUp, name="SignUp"),
    path('sign-in', views.SignIn, name="SignIn"),

    path('master/dashboard/<str:code>', views.AdminDashboard, name="AdminDashboard"),

    path('master/all-orders/<str:code>', views.AdminOrders, name="AdminOrders"),
    path('master/view-order/<str:code>/<str:cid>', views.AdminViewOrder, name="AdminViewOrder"),
    path('master/edit-order/<str:code>', views.AdminEditOrder, name="AdminEditOrder"),
    path("master/orders/<str:code>/create-shipment/", views.AdminCreateShipment, name="AdminCreateShipment"),
    path("master/orders/<str:code>/assign-awb/", views.AdminAssignAWB, name="AdminAssignAWB"),
    path("master/orders/<str:code>/refresh-tracking/", views.AdminRefreshTracking, name="AdminRefreshTracking"),
    path("master/orders/<str:code>/send-tracking-email/", views.AdminSendTrackingEmail, name="AdminSendTrackingEmail"),
    path("master/orders/<str:code>/generate-pickup/", views.AdminGeneratePickup, name="AdminGeneratePickup"),
    path("master/orders/<str:code>/generate-label/", views.AdminGenerateLabel, name="AdminGenerateLabel"),
    path("master/orders/<str:code>/generate-invoice/", views.AdminGenerateInvoice, name="AdminGenerateInvoice"),
    path("master/orders/invoice-details/<str:code>", views.AdminViewInvoice, name="AdminViewInvoice"),
    path("master/orders/email-invoice/<str:code>", views.AdminEmailInvoice, name="AdminEmailInvoice"),
    path('master/cancel-order/<str:code>', views.AdminCancelOrder, name="AdminCancelOrder"),
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
    path("master/add-blog-category/<str:code>", views.AdminNewBlogCategory, name="AdminNewBlogCategory"),
    path("master/edit-blog-category/<str:code>/", views.AdminEditBlogCategory, name="AdminEditBlogCategory"),
    path("master/delete-blog-category/<str:code>/", views.AdminDeleteBlogCategory, name="AdminDeleteBlogCategory"),

    path('master/all-blogs/<str:code>', views.AdminBlogs, name="AdminBlogs"),
    path('master/add-new-blog/<str:code>', views.AdminAddNewBlog, name="AdminAddNewBlog"),
    path("master/edit-blog/<str:code>/<str:slug>", views.AdminEditBlog, name="AdminEditBlog"),
    path("master/delete-blog/<str:code>/", views.AdminDeleteBlog, name="AdminDeleteBlog"),

    path('master/account-settingss/<str:code>', views.AdminAccSettings, name="AdminAccSettings"),

    path('master/notifications/<str:code>', views.AdminNotifications, name="AdminNotifications"),

    path('master/reports/<str:code>', views.AdminReports, name="AdminReports"),
    path('master/reports/insights/<str:code>', views.AdminReportsInsights, name="AdminReportsInsights"),
    path('master/reports/sales/<str:code>', views.AdminReportsSales, name="AdminReportsSales"),
    path('master/reports/orders/<str:code>', views.AdminReportsOrders, name="AdminReportsOrders"),
    path('master/reports/customers/<str:code>', views.AdminReportsCustomers, name="AdminReportsCustomers"),
    path('master/reports/products/<str:code>', views.AdminReportsProducts, name="AdminReportsProducts"),
    path('master/reports/payments/<str:code>', views.AdminReportsPayments, name="AdminReportsPayments"),
    path('master/reports/shipments/<str:code>', views.AdminReportsShipments, name="AdminReportsShipments"),
    path('master/reports/notifications/<str:code>', views.AdminReportsNotifications, name="AdminReportsNotifications"),
    path('master/reports/chatbot/<str:code>', views.AdminReportsChatbot, name="AdminReportsChatbot"),

    path('master/recommendation-engine/chat-keywords/<str:code>', views.AdminChatKeywords, name="AdminChatKeywords"),
    path('master/recommendation-engine/add-chat-keywords/<str:code>', views.AdminAddChatKeywords, name="AdminAddChatKeywords"),
    path('master/recommendation-engine/update-chat-keywords/<str:code>', views.AdminUpdateChatKeywords, name="AdminUpdateChatKeywords"),
    path('master/recommendation-engine/delete-chat-keywords/<str:code>', views.AdminDeleteChatKeywords, name="AdminDeleteChatKeywords"),

    path('master/recommendation-engine/faqs/<str:code>', views.AdminFaqs, name="AdminFaqs"),
    path('master/recommendation-engine/add-faq/<str:code>', views.AdminAddFaq, name="AdminAddFaq"),
    path('master/recommendation-engine/update-faq/<str:code>', views.AdminUpdateFaq, name="AdminUpdateFaq"),
    path('master/recommendation-engine/delete-faq/<str:code>', views.AdminDeleteFaq, name="AdminDeleteFaq"),

    path('master/recommendation-engine/suggestion-map/<str:code>', views.AdminSuggestMap, name="AdminSuggestMap"),
    path('master/recommendation-engine/add-suggestion-map/<str:code>', views.AdminAddSuggestMap, name="AdminAddSuggestMap"),
    path('master/recommendation-engine/update-suggestion-map/<str:code>', views.AdminUpdateSuggestMap, name="AdminUpdateSuggestMap"),
    path('master/recommendation-engine/delete-suggestion-map/<str:code>', views.AdminDeleteSuggestMap, name="AdminDeleteSuggestMap"),

    path('master/recommendation-engine/news-and-events/<str:code>', views.AdminMedias, name="AdminMedias"),
    path('master/recommendation-engine/add-media/<str:code>', views.AdminAddMedia, name="AdminAddMedia"),
    path('master/recommendation-engine/update-media/<str:code>', views.AdminUpdateMedia, name="AdminUpdateMedia"),
    path('master/recommendation-engine/delete-media/<str:code>', views.AdminDeleteMedia, name="AdminDeleteMedia"),

    path('master/recommendation-engine/support-tickets/<str:code>', views.AdminSupportTickets, name='AdminSupportTickets'),
    path('master/recommendation-engine/create-support-ticket/<str:code>', views.AdminCreateSupportTicket, name='AdminCreateSupportTicket'),
    path('master/recommendation-engine/update-support-ticket/<str:code>', views.AdminUpdateSupportTicket, name='AdminUpdateSupportTicket'),
    path('master/recommendation-engine/delete-support-ticket/<str:code>', views.AdminDeleteSupportTicket, name='AdminDeleteSupportTicket'),

    

    path('sign-out', views.SignOut, name="SignOut"),
]