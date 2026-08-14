from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BootstrapView,
    CheckoutView,
    LoginView,
    LogoutView,
    MeView,
    ProductViewSet,
    RefundView,
    ReportsView,
    SettingsView,
    TransactionViewSet,
    export_backup,
    health,
    reset_history,
    reset_stock,
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='products')
router.register('transactions', TransactionViewSet, basename='transactions')

urlpatterns = [
    path('health/', health),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('me/', MeView.as_view()),
    path('bootstrap/', BootstrapView.as_view()),
    path('checkout/', CheckoutView.as_view()),
    path('refunds/', RefundView.as_view()),
    path('reports/', ReportsView.as_view()),
    path('settings/', SettingsView.as_view()),
    path('export/', export_backup),
    path('reset/stock/', reset_stock),
    path('reset/history/', reset_history),
]

urlpatterns += router.urls
