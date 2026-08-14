from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product, ProductSize, Store, Transaction, TransactionItem
from .serializers import ProductSerializer, SettingsSerializer, TransactionSerializer


def role_from_request(request):
    user = request.user
    if not user.is_authenticated:
        return ''
    if user.is_superuser or user.is_staff:
        return 'admin'
    return 'cashier'


def store_from_role(role):
    return 'main'


ACTIVE_PAYMENT_METHODS = (Transaction.PAYMENT_CASH, Transaction.PAYMENT_QR)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Неверный логин или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'error': 'Пользователь отключен'}, status=status.HTTP_403_FORBIDDEN)

        login(request, user)
        role = role_from_request(request)
        return Response({
            'id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'role': role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        })


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'success': True})


class MeView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'user': None})
        return Response({'user': {
            'id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'role': role_from_request(request),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }})


class BootstrapView(APIView):
    def get(self, request):
        return Response({
            'settings': SettingsSerializer.build(),
            'categories': [choice[0] for choice in Product.CATEGORY_CHOICES],
            'payment_methods': [
                {'code': code, 'name': name}
                for code, name in Transaction.PAYMENT_CHOICES
                if code in ACTIVE_PAYMENT_METHODS
            ],
        })


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.prefetch_related('sizes').filter(is_active=True)

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q')
        category = self.request.query_params.get('category')

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(barcode__icontains=query))
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        return queryset

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.is_active = False
        product.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.select_related('store', 'related_transaction').prefetch_related('items')

    def get_queryset(self):
        queryset = super().get_queryset()
        tx_type = self.request.query_params.get('type')
        tx_date = self.request.query_params.get('date')

        if tx_type and tx_type != 'all':
            queryset = queryset.filter(type=tx_type)
        if tx_date:
            queryset = queryset.filter(created_at__date=tx_date)
        return queryset


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutView(APIView):
    @transaction.atomic
    def post(self, request):
        store, _ = Store.objects.select_for_update().get_or_create(code='main', defaults={'name': 'ZARA KIDS'})
        cart = request.data.get('cart', [])
        payment_method = request.data.get('payment_method')
        cashier_name = request.data.get('cashier_name') or request.user.get_full_name() or request.user.username

        if payment_method not in ACTIVE_PAYMENT_METHODS:
            return Response({'error': 'Неверный способ оплаты'}, status=400)
        if not cart:
            return Response({'error': 'Корзина пуста'}, status=400)

        locked_sizes = {}
        total_amount = 0
        total_cost = 0

        for item in cart:
            size_id = item.get('size_id')
            qty = int(item.get('quantity', 0))
            if qty <= 0:
                return Response({'error': 'Количество должно быть больше нуля'}, status=400)

            size = ProductSize.objects.select_for_update().select_related('product').get(id=size_id)
            if not size.has_stock(qty):
                return Response({
                    'error': f'Недостаточно товара "{size.product.name}" ({size.size})'
                }, status=400)

            locked_sizes[size_id] = (size, qty)
            total_amount += size.product.retail_price * qty
            total_cost += size.product.cost_price * qty

        tx = Transaction.objects.create(
            number=f'tx-{int(timezone.now().timestamp() * 1000)}',
            store=store,
            type=Transaction.TYPE_SALE,
            cashier_name=cashier_name,
            total_amount=total_amount,
            total_cost=total_cost,
            payment_method=payment_method,
        )

        for size, qty in locked_sizes.values():
            size.add_stock(-qty)
            size.save(update_fields=['stock'])
            TransactionItem.objects.create(
                transaction=tx,
                product=size.product,
                product_name=size.product.name,
                size=size.size,
                price=size.product.retail_price,
                cost=size.product.cost_price,
                quantity=qty,
            )

        return Response(TransactionSerializer(tx).data, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class RefundView(APIView):
    @transaction.atomic
    def post(self, request):
        role = role_from_request(request)
        if role != 'admin':
            return Response({'error': 'Только администратор может оформлять возврат'}, status=403)

        number = request.data.get('number')
        tx = Transaction.objects.select_for_update().prefetch_related('items').get(number=number)
        if tx.type != Transaction.TYPE_SALE:
            return Response({'error': 'Возврат возможен только по продаже'}, status=400)
        if hasattr(tx, 'refund'):
            return Response({'error': 'Этот чек уже возвращен'}, status=400)

        refund = Transaction.objects.create(
            number=f'rf-{int(timezone.now().timestamp() * 1000)}',
            store=tx.store,
            type=Transaction.TYPE_REFUND,
            cashier_name=tx.cashier_name,
            total_amount=tx.total_amount,
            total_cost=tx.total_cost,
            payment_method=tx.payment_method,
            related_transaction=tx,
            authorized_by=request.data.get('authorized_by', 'Администратор'),
        )

        for item in tx.items.all():
            size = ProductSize.objects.select_for_update().filter(product=item.product, size=item.size).first()
            if size:
                size.add_stock(item.quantity)
                size.save(update_fields=['stock'])
            TransactionItem.objects.create(
                transaction=refund,
                product=item.product,
                product_name=item.product_name,
                size=item.size,
                price=item.price,
                cost=item.cost,
                quantity=item.quantity,
            )

        return Response(TransactionSerializer(refund).data, status=201)


class ReportsView(APIView):
    def get(self, request):
        period = request.query_params.get('period', 'today')
        queryset = Transaction.objects.select_related('store')
        now = timezone.now()

        if period == 'today':
            queryset = queryset.filter(created_at__date=now.date())
        elif period == '7days':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        elif period == 'month':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=30))

        metrics = {
            'total_revenue': 0,
            'total_profit': 0,
            'sale_count': 0,
            'refund_count': 0,
            'avg_check': 0,
            'stock_cost': 0,
            'stock_retail': 0,
        }

        for tx in queryset:
            sign = 1 if tx.type == Transaction.TYPE_SALE else -1
            if tx.type == Transaction.TYPE_SALE:
                metrics['sale_count'] += 1
            else:
                metrics['refund_count'] += 1
            profit = tx.total_amount - tx.total_cost
            metrics['total_revenue'] += sign * tx.total_amount
            metrics['total_profit'] += sign * profit

        if metrics['sale_count']:
            metrics['avg_check'] = round(metrics['total_revenue'] / metrics['sale_count'])

        for product in Product.objects.prefetch_related('sizes').filter(is_active=True):
            for size in product.sizes.all():
                total_stock = max(0, size.stock)
                metrics['stock_cost'] += total_stock * product.cost_price
                metrics['stock_retail'] += total_stock * product.retail_price

        return Response(metrics)


@method_decorator(csrf_exempt, name='dispatch')
class SettingsView(APIView):
    def get(self, request):
        return Response(SettingsSerializer.build())

    def patch(self, request):
        store, _ = Store.objects.get_or_create(code='main', defaults={'name': 'ZARA KIDS'})
        if request.data.get('store_name'):
            store.name = request.data['store_name']
            store.save(update_fields=['name'])

        return Response(SettingsSerializer.build())


@api_view(['POST'])
@csrf_exempt
def reset_stock(request):
    if role_from_request(request) != 'admin':
        return Response({'error': 'Forbidden'}, status=403)
    Product.objects.all().delete()
    return Response({'success': True})


@api_view(['POST'])
@csrf_exempt
def reset_history(request):
    if role_from_request(request) != 'admin':
        return Response({'error': 'Forbidden'}, status=403)
    Transaction.objects.all().delete()
    return Response({'success': True})


def export_backup(request):
    return JsonResponse({
        'settings': SettingsSerializer.build(),
        'products': ProductSerializer(Product.objects.prefetch_related('sizes').all(), many=True, context={'request': request}).data,
        'transactions': TransactionSerializer(Transaction.objects.prefetch_related('items').all(), many=True).data,
    })
