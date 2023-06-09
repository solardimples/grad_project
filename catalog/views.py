from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib.auth import login, authenticate
from .forms import *


# Функция обрабатывает содержимое главной страницы
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

    def get_queryset(self):
        """
        Метод генерирует список товаров в зависимости от предоставленных фильтров
        """
        queryset = super().get_queryset()
        filter_values = self.get_filter_values(no_pks=True)

        for key, value in filter_values.items():
            if value:
                queryset = queryset.filter(**{key: value})

        return queryset.order_by('-date_added')

    def get_context_data(self, **kwargs):
        """
        Метод генерирует переменные для контекста страницы
        """
        context = super().get_context_data(**kwargs)
        filter_values = self.get_filter_values()
        context['category'] = filter_values.pop('category')  # генерация названия категории на странице
        context['form'] = ProductFilterForm(filter_values)  # генерация формы фильтрации товаров
        context['paginator_range'] = context['page_obj'].paginator.get_elided_page_range(
            number=context['page_obj'].number, on_each_side=2, on_ends=1
        )  # генерация динамического elided_page_range
        return context

    def get_filter_values(self, no_pks=False):
        """
        Метод возвращает примененные к списку товаров фильтры
        """
        category = Category.objects.filter(add_name=self.kwargs.get('category'))
        filter_values = {'category': category[0] if category else None}
        add_keys = ['gender', 'brand']

        if no_pks:
            filter_values.update({key + '__in': self.request.GET.getlist(key) for key in add_keys})
        else:
            filter_values.update({'selected_pks': list(map(str, self.get_queryset().values_list('pk', flat=True)))})
            filter_values.update({'selected_' + key: self.request.GET.getlist(key) for key in add_keys})

        return filter_values


# Класс обрабатывает работу со страницей конкретного товара (шаблон "product_detail.html", ключ "product")
class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        """
        Метод генерирует переменные для контекста страницы
        """
        context = super().get_context_data(**kwargs)
        context.update(self.generate_form_context())  # генерация формы добавления товара в корзину
        context.update(self.generate_review_context())  # генерация формы отзыва и отзывов
        return context

    def generate_form_context(self):
        instance_objects = ProductInstance.objects.filter(product_id=self.kwargs.get('pk'), status_id=1)
        if instance_objects:
            return {'form': ProductCartForm(instance_objects=instance_objects)}
        else:
            return {'sold_out': 'Товар отсутствует на складе.'}

    def generate_review_context(self):
        queryset = Product.objects.get(id=self.kwargs.get('pk')).review_set.all()
        paginator = Paginator(queryset, 2)  # paginate_by
        page = paginator.get_page(self.request.GET.get('page'))
        return {
            'review_form': ReviewForm(),
            'paginator': paginator,
            'page_obj': page,
            'paginator_range': page.paginator.get_elided_page_range(number=page.number, on_each_side=2, on_ends=1)
        }


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

        return {
            'order_items': order_items_filtered,
            'order_item_items': order_item_items,
            'common': 'common/order_list.html'
        }

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

        return {'order': order, 'order_items': order_items, 'common': 'common/order_detail.html'}

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


class ReviewManager:
    @staticmethod
    def add(request, product_id):
        form = ReviewForm(data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['product'] = Product.objects.get(id=product_id)
            data['user'] = request.user
            Review.objects.create(**data)
        return redirect(request.META.get('HTTP_REFERER', '/'))

    @staticmethod
    def delete(request):
        pass

    @staticmethod
    def get(request):
        pass
