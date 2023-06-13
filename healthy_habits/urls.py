"""
URL configuration for healthy_habits project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from catalog import views
from django.contrib.auth import views as auth_views
from catalog.forms import CustomPasswordResetForm, CustomSetPasswordForm


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # главная страница
    # Маршруты для работы с администрацией сайта
    path('admin-database', views.AdminManager.admin_database, name='admin_database'),  # управление БД (админка)
    path('admin-promos', views.AdminManager.admin_promos, name='admin_promos'),  # управление акциями (админка)
    path('admin-orders', views.AdminManager.admin_orders, name='admin_orders'),  # управление заказами (админка)
    path('admin-users', views.AdminManager.admin_users, name='admin_users'),  # управление заказами (админка)
    # Маршруты для работы с каталогом товаров
    path('catalog', views.ProductListView.as_view(), name='catalog'),  # каталог всех товаров
    path('catalog/<str:category>', views.ProductListView.as_view(), name='category'),  # каталог категории товаров
    path('catalog/<str:category>/<int:pk>', views.ProductDetailView.as_view(), name='product'),  # страница товара
    # Маршруты для работы с заказами
    path('add/<int:product_id>', views.OrderManager.add_to_cart, name='add'),  # добавить товар в корзину
    path('delete/<int:cartitem_id>', views.OrderManager.delete_from_cart, name='delete'),  # удалить товар из корзины
    path('order-processing', views.OrderManager.process_order, name='process_order'),  # оформить заказ
    path('orders', views.OrderManager.manage_orders, name='manage_orders'),  # управление заказами
    path('orders/<str:action>/<int:pk>', views.OrderManager.update_order, name='update_order'),  # обновить статус заказа
    # Маршруты для работы с аккаунтами пользователей
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login', views.UserManager.login, name='login'),  # авторизация
    path('accounts/register', views.UserManager.register, name='register'),  # регистрация
    path('accounts/password-reset', auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            form_class=CustomPasswordResetForm), name='password_reset'),   # инициация сброса пароля
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        form_class=CustomSetPasswordForm), name='password_reset_confirm'),  # сброс пароля
    # Маршруты для работы с отзывами
    path('add/review/<int:product_id>', views.ReviewManager.add, name='add_review'),  # добавить отзыв
    path('delete/review/<int:review_id>', views.ReviewManager.delete, name='delete_review'),  # удалить отзыв
]

