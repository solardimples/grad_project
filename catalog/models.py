from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
"""
* статус заказа (OrderStatus): name
Заказы (Order): user_id (ForeignKey), status, total_price
Состав заказа (OrderItem): order_id (ForeignKey), productinstance_id (ForeignKey), quantity, price 
----
Отзывы (Review): user_id (ForeignKey), product_id (ForeignKey), text, rating, date_created
"""

# Таблица "Пользователи" (Users) <- встроенная
# id (Primary Key), username, email, password, first_name, last_name, is_staff, is_active, date_joined


# *категория (Category): name
class Category(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']


# *пол (Gender): name
class Gender(models.Model):
    name = models.CharField(verbose_name='Название', max_length=10)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'пол'
        verbose_name_plural = 'пол'
        ordering = ['name']


# *бренд (Brand) name, description, logo
class Brand(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    image = models.ImageField(verbose_name='Изображение', upload_to='static/images/brand_logos', null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'
        ordering = ['name']


# Товары (Product): name, description, price, *brand (ForeignKey), *category (ForeignKey), *gender (ForeignKey), image,
# date_created
class Product(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, verbose_name='Пол', null=True, blank=True)
    description = models.TextField(verbose_name='Описание', max_length=1000)
    price = models.FloatField(verbose_name='Цена')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='Бренд')
    image = models.ImageField(verbose_name='Изображение', upload_to='static/images/product_photos')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    @staticmethod
    def get_category(category, ru_keys=False, pk=False):
        """
        Метод возвращает категорию на русском, английском или в виде id
        """
        data = {'en': ('wear', 'shoes', 'equipment'), 'ru': ('Одежда', 'Обувь', 'Снаряжение'), 'pk': (1, 2, 3)}
        keys = data['ru'] if ru_keys else data['en']
        values = data['pk'] if pk else data['en'] if ru_keys else data['ru']
        dct = {k: v for k, v in zip(keys, values)}
        return dct.get(category)

    def get_url(self):
        """
        Метод возвращает абсолютную ссылку на товар
        """
        return f'/catalog/{self.get_category(category=str(self.category), ru_keys=True)}/{self.pk}'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['date_updated']


# *размер (Size): name
class Size(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'размер'
        verbose_name_plural = 'размеры'
        ordering = ['name']


# *накладная (Invoice): number, date, date_created
class Invoice(models.Model):
    number = models.CharField(verbose_name='Номер инвойса', max_length=50)
    date = models.DateField(verbose_name='Дата инвойса', default=timezone.now)
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    def __str__(self):
        return f'{self.date} {self.number}'

    class Meta:
        verbose_name = 'инвойс'
        verbose_name_plural = 'инвойсы'
        ordering = ['date']


# *статус экземпляра товара (ProductInstanceStatus): name
class ProductInstanceStatus(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'статус экземпляра товара'
        verbose_name_plural = 'статусы экземпляров товаров'
        ordering = ['name']


# Экземпляры товаров (ProductInstance): product_id (ForeignKey), *size (ForeignKey), quantity, *invoice (ForeignKey),
# purchase_price, *status (ForeignKey), date_created
class ProductInstance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Размер')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name='Инвойс')
    purchase_price = models.FloatField(verbose_name='Цена закупки')
    status = models.ForeignKey(ProductInstanceStatus, on_delete=models.CASCADE, verbose_name='Статус')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk is not None:
            self.status_id = 1 if self.check_availability() else 2
            self.save()

    def __str__(self):
        return f'{self.pk} {self.product.name}'

    def check_availability(self):
        order_items = OrderItem.objects.filter(productinstance=self)
        order_items_count = order_items.count() - order_items.filter(order__status_id=4).count()
        return True if self.quantity > order_items_count else False

    class Meta:
        verbose_name = 'экземпляр товара'
        verbose_name_plural = 'экземпляры товаров'


# Корзина (Cart): user_id (OneToOneField), guest_id(OneToOneField)
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    def total_price(self):
        cart_items = CartItem.objects.filter(cart=self)
        product_instances = [item.productinstance for item in cart_items if item.quantity > 0]
        product_items = [item.product for item in product_instances]
        price = [item.price for item in product_items]
        return sum(price)

    def total_quantity(self):
        cart_items = CartItem.objects.filter(cart=self)
        quantity = [item.quantity for item in cart_items]
        return sum(quantity)


# Состав корзины (CartItem): cart_id (ForeignKey), productinstance_id (ForeignKey), quantity
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина')
    productinstance = models.ForeignKey(ProductInstance, on_delete=models.CASCADE, verbose_name='Экземпляр Товара')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()


# * статус заказа (OrderStatus): name
class OrderStatus(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'статус заказа'
        verbose_name_plural = 'статусы заказов'
        ordering = ['name']


# Заказы (Order): user (ForeignKey), status (ForeignKey), details, delivery_price
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE, verbose_name='Статус')
    details = models.JSONField(verbose_name='Данные')
    delivery_price = models.PositiveIntegerField(verbose_name='Стоимость доставки')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()

    def total_price(self):
        order_items = OrderItem.objects.filter(order=self)
        price = [item.price for item in order_items]
        return sum(price)

    def final_price(self):
        total_price = self.total_price()
        return sum([total_price, self.delivery_price])

    def total_quantity(self):
        order_items = OrderItem.objects.filter(order=self)
        quantity = [item.quantity for item in order_items]
        return sum(quantity)

    def __str__(self):
        return f'Заказ {self.pk}'

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


# Состав заказа (OrderItem): order (ForeignKey), productinstance (ForeignKey), size, quantity, price
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ')
    productinstance = models.ForeignKey(ProductInstance, on_delete=models.CASCADE, verbose_name='Экземпляр Товара')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name='Размер')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    date_added = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    date_updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    objects = models.Manager()
