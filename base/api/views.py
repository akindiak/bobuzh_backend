import json
from django.http import JsonResponse

from django.contrib.auth.models import User
from base.models import Category, Product, Order, OrderItem, Customer, ProductRating
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser

from .serializers import (
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    CategorySerializer,
    ProductSerializer,
    CustomerSerializer,
    OrderSerializer,
    OrderItemSerializer,
    ProductRatingSerializer,
    ProductImageSerializer,
)
from rest_framework import generics, status, viewsets, serializers
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework.decorators import api_view, action, authentication_classes, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken


@api_view(['GET'])
def get_routes(request):
    routes = [
        'api/auth/register/',
        'api/auth/login/',
        'api/auth/token/refresh/',
        'api/auth/logout/',
        'api/auth/logout-all/',
        'api/store/categories/',
        'api/store/categories/<id>/',
        'api/store/products/',
        'api/store/products/<id>/',
        'api/store/products/<id>/add_rating/',
        'api/store/products/<id>/upload_image/'
    ]
    return Response(routes)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        tokens = OutstandingToken.objects.filter(user_id=request.user_id)
        for token in tokens:
            t, _ = BlacklistedToken.objects.get_or_create(token=token)

        return Response(status=status.HTTP_205_RESET_CONTENT)


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)

    # def get_queryset(self):
    #     queryset = Category.objects.all()
    #     if params := self.request.query_params:
    #         params = params.dict()
    #         queryset = queryset.filter(**params)
    #     return queryset


class CategoryRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        queryset = Product.objects.all()
        if params := self.request.query_params:
            params = params.dict()
            params.pop('limit', None)
            params.pop('offset', None)
            if specifications := params.pop('specifications', None):
                specifications = json.loads(specifications)
                for option in specifications.get("options"):
                    queryset = queryset.filter(productspecification__option=option)

            queryset = queryset.filter(**params)
        return queryset

    @action(detail=True, methods=['put'], permission_classes=(IsAuthenticated,))
    def add_rating(self, request, pk):
        user = self.request.user
        product = self.get_object()
        serializer = ProductRatingSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            rating, created = ProductRating.objects.update_or_create(
                user=user,
                product=product,
                defaults={"score": serializer.validated_data['score']}
            )
            product_sz = self.get_serializer(instance=product)
            if created:
                return Response(product_sz.data, status=status.HTTP_201_CREATED)
            return Response(product_sz.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'patch', 'put'],
            permission_classes=(IsAdminUser,), serializer_class=ProductImageSerializer)
    def upload_image(self, request, pk):
        product = self.get_object()
        try:
            image = request.FILES['image']
        except KeyError:
            return Response("image is not provided", status=status.HTTP_400_BAD_REQUEST)

        if product.image:
            product.image.delete(False)

        product.image = image
        product.save()
        return Response('Image was uploaded')


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        input_data = self.request.data
        # {"products": [{"product": 2, "quantity": 3}, {"product": 3, "quantity": 4}], "customer" {"email": "..."}}

        customer = input_data.get('customer')
        if not customer:
            return Response(
                {'non customer error': 'Customer data is not provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sz_customer = CustomerSerializer(data=customer)
        if sz_customer.is_valid():
            instance, created = sz_customer.get_or_create()
            if not created:
                sz_customer.update(instance, sz_customer.validated_data)
        else:
            return Response(sz_customer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(customer=instance)

        products = input_data.get("products", [])
        if not products:
            order.delete()
            return Response(
                {'non products error': 'Products data is not provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for product in products:
            product['order'] = order.id

        sz_product_item = OrderItemSerializer(data=products, many=True)
        if not sz_product_item.is_valid():
            order.delete()
            return Response(
                {'product errors': sz_product_item.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        sz_product_item.save()

        order.calculate_total_price()
        order.set_unique_id()
        order_sz = self.get_serializer(instance=order)
        return Response(order_sz.data, status=status.HTTP_201_CREATED)
