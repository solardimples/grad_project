from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib.auth import login, authenticate
from .forms import *


def index(request):
    """
    Функция обрабатывает отображение главной страницы
    """
    # генерация товаров для карусели новинок
    new_products = Product.objects.order_by('-date_added')[:6]

    context = {'new_products': new_products}
    return render(request, 'index.html', context=context)


# Класс обрабатывает работу с каталогом товаров (шаблон "product_list.html", ключ "product_list")
class ProductListView(ListView):
    model = Product
    paginate_by = 12
    form_class = ProductFilterForm

    def get_queryset(self):
        """
        Метод генерирует список товаров в зависимости от предоставленных фильтров
        """
        queryset = super().get_queryset()
        category = self.kwargs.get('category')
        gender = self.request.GET.getlist('gender')
        brand = self.request.GET.getlist('brand')

        queryset = queryset.filter(category=Product.get_category(category=category, pk=True)) if category else queryset
        queryset = queryset.filter(gender__in=gender) if gender else queryset
        queryset = queryset.filter(brand__in=brand) if brand else queryset

        return queryset.order_by('-date_added')

    def get_context_data(self, **kwargs):
        """
        Метод генерирует переменные для контекста страницы
        """
        context = super().get_context_data(**kwargs)
        # генерация названия категории на странице
        category = self.kwargs.get('category')
        context['category'] = Product.get_category(category=category)
        context['category'] = 'Каталог' if not context['category'] else context['category']
        # генерация формы фильтрации товаров
        selected_pks = list(map(str, self.get_queryset().values_list('pk', flat=True)))  # список ключей товаров
        selected_gender = self.request.GET.getlist('gender')  # список выбранных фильтров пола
        selected_brand = self.request.GET.getlist('brand')  # список выбранных фильтров бренда
        context['form'] = ProductFilterForm(
            selected_pks=selected_pks, selected_gender=selected_gender, selected_brand=selected_brand
        )
        # генерация динамического elided_page_range
        page = context['page_obj']
        context['paginator_range'] = page.paginator.get_elided_page_range(number=page.number, on_each_side=2, on_ends=1)
        context['common'] = 'common/pagination.html'
        return context


# Класс обрабатывает работу со страницей конкретного товара (шаблон "product_detail.html", ключ "product")
class ProductDetailView(DetailView):
    model = Product
    form_class = ProductCartForm

    def get_context_data(self, **kwargs):
        """
        Метод генерирует переменные для контекста страницы
        """
        context = super().get_context_data(**kwargs)
        # генерация названия категории на странице
        category = self.kwargs.get('category')
        pk = self.kwargs.get('pk')
        context['pk'] = pk
        context['category'] = Product.get_category(category=category)
        context['category_link'] = f'/catalog/{category}'
        # генерация формы с размерами конкретного товара
        instance_objects = ProductInstance.objects.filter(product_id=pk, status_id=1)
        if instance_objects:
            context['form'] = ProductCartForm(instance_objects=instance_objects)
        else:
            context['sold_out'] = 'Товар отсутствует на складе.'
        # генерация формы отзыва
        context['review_form'] = ReviewForm()
        return context


# Класс содержит методы для работы с корзиной и заказами
class OrderManager:

    @staticmethod
    def add_to_cart(request, product_id):
        """
        Метод добавляет товар в корзину
        """
        if not request.user.is_authenticated:
            return redirect('login')

        data = {}
        product = Product.objects.get(id=product_id)

        data['cart'], created = Cart.objects.get_or_create(user=request.user)
        data['productinstance'] = ProductInstance.objects.filter(product=product, size=request.POST.get('size')).first()

        CartItem.objects.create(**data)
        return redirect(product.get_url())

    @staticmethod
    def delete_from_cart(request, cartitem_id):
        """
        Метод удаляет товар из корзины и саму корзину, если в ней нет товара
        """
        CartItem.objects.filter(id=cartitem_id).delete()

        cart = Cart.objects.get(user=request.user)
        if not CartItem.objects.filter(cart=cart):
            cart.delete()

        return redirect(request.META.get('HTTP_REFERER', '/'))

    @staticmethod
    def process_order(request):
        """
        Метод обрабатывает заказ
        """
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return redirect('catalog')

        cart = Cart.objects.get(user=request.user)
        form = OrderDetails()

        context = {
            'cart': cart,
            'cart_items': cart.cartitem_set.all(),
            'delivery_price': 0,
            'delivery_time': 'от 2 до 10 дней'
        }

        context['final_price'] = cart.total_price() + context['delivery_price']

        if request.method == 'POST':
            form = OrderDetails(data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                OrderManager.create_order(request, data, context)
                return redirect('catalog')

        context['form'] = form
        return render(request, 'profile/cart.html', context=context)

    @staticmethod
    def create_order(request, data, context):
        """
        Метод создает заказ
        """
        order = {
            'user': request.user,
            'status': OrderStatus(id=1),
            'details': data,
            'delivery_price': context['delivery_price']
        }

        order = Order.objects.create(**order)

        for item in context['cart_items']:
            productinstance = item.productinstance

            if productinstance.check_availability():
                order_item = {
                    'order': order,
                    'productinstance': productinstance,
                    'size': productinstance.size,
                    'quantity': item.quantity,
                    'price': productinstance.product.price
                }
                OrderItem.objects.create(**order_item)
                item.delete()
            else:
                productinstance.status_id = 2
                productinstance.save()

        if not Cart.objects.get(user=request.user).cartitem_set.all():
            Cart.objects.get(user=request.user).delete()

    @staticmethod
    def manage_orders(request):
        """
        Метод обрабатывает существующие заказы
        """
        if not request.user.is_authenticated:
            return redirect('login')

        context = OrderManager.manage_one(request) if request.GET.get('pk') else OrderManager.manage_multiple(request)

        return render(request, 'profile/orders.html', context)

    @staticmethod
    def manage_multiple(request, admin=False):
        """
        Метод возвращает словарь с данными о заказах
        """
        order_items = Order.objects.all() if admin else Order.objects.filter(user=request.user)

        order_items_filtered = []
        for status in OrderStatus.objects.all():
            order_items_filtered.append(
                {'name': status.name.capitalize(), 'items': order_items.filter(status_id=status.id)}
            )

        order_item_items = {}
        for item in order_items:
            order_item_items[item] = OrderItem.objects.filter(order=item)

        context = {
            'order_items': order_items_filtered,
            'order_item_items': order_item_items,
            'common': 'common/order_list.html'
        }
        return context

    @staticmethod
    def manage_one(request, admin=False):
        """
        Метод возвращает словарь с данными одного заказа
        """
        pk = request.GET.get('pk')

        if not admin:
            try:
                Order.objects.get(id=pk, user=request.user)
            except Order.DoesNotExist:
                return redirect('/')

        order = Order.objects.get(id=pk)
        order_items = OrderItem.objects.filter(order=order)

        context = {'order': order, 'order_items': order_items, 'common': 'common/order_detail.html'}
        return context

    @staticmethod
    def update_order(request, action, pk):
        """
        Метод обновляет статус заказа
        """
        order = Order.objects.get(id=pk)
        if action == 'process':
            if order.status_id == 4:
                order_items = OrderItem.objects.filter(order=order)
                for item in order_items:
                    same_items = OrderItem.objects.filter(productinstance=item.productinstance)

                    same_items_in_order = order.orderitem_set.filter(productinstance=item.productinstance).count()
                    same_items_filtered = same_items.count() - same_items.filter(order__status_id=4).count()

                    item_quantity = same_items_in_order + same_items_filtered

                    if item.productinstance.quantity < item_quantity:
                        item.delete()

                    if not item.productinstance.check_availability():
                        item.delete()
            order.status_id = 1
        elif action == 'ready':
            order.status_id = 2
        elif action == 'complete':
            order.status_id = 3
        elif action == 'cancel':
            order.status_id = 4
        order.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))


# Класс содержит методы для администрации сайта
class AdminManager:

    @staticmethod
    def admin_database(request):
        context = {}
        return render(request, 'admin/database.html', context)

    @staticmethod
    def admin_promos(request):
        context = {}
        return render(request, 'admin/promos.html', context)

    @staticmethod
    def admin_orders(request):
        if not request.user.is_superuser:
            return redirect('/')

        if request.GET.get('pk'):
            context = OrderManager.manage_one(request, admin=True)
        else:
            context = OrderManager.manage_multiple(request, admin=True)

        return render(request, 'admin/orders.html', context)

    @staticmethod
    def admin_users(request):
        context = {}
        return render(request, 'admin/users.html', context)


# Класс содержит методы для работы с аккаунтами пользователей
class UserManager:

    @staticmethod
    def login(request):
        """
        Метод обрабатывает авторизацию пользователей
        """
        context = {}
        form = LoginForm()

        context['redirect_page'] = request.GET.get('next', reverse('index'))
        if request.method == 'POST':
            form = LoginForm(data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                user = authenticate(request, username=data['username'], password=data['password'])
                login(request, user)
                return redirect(context['redirect_page'])

        context['form'] = form
        return render(request, 'registration/login.html', context=context)

    @staticmethod
    def register(request):
        """
        Метод обрабатывает регистрацию пользователей
        """
        context = {}
        form = RegisterForm()

        context['redirect_page'] = request.GET.get('next', reverse('index'))

        if request.method == 'POST':
            form = RegisterForm(data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                user = User.objects.create_user(data['username'], data['email'], data['password1'])
                login(request, user)
                return redirect(context['redirect_page'])

        context['form'] = form
        return render(request, 'registration/register.html', context=context)


