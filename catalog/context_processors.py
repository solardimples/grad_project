from .models import Cart, ProductInstance


def create_admin_pages(request, context):
    if request.user.is_superuser:
        context['admin_pages'] = [
            {'title': 'Акции', 'link': '/admin-promos'},
            {'title': 'База данных', 'link': '/admin-database'},
            {'title': 'Заказы', 'link': '/admin-orders'},
            {'title': 'Пользователи', 'link': '/admin-users'},
        ]
    return context


def create_cart_table(request, context):
    user = request.user
    try:
        cart = Cart.objects.get(user=user)
        cart_items = cart.cartitem_set.all()
        for item in cart_items:
            productinstance = item.productinstance
            if productinstance.check_availability():
                item.quantity = 1
            else:
                new_productinstance = ProductInstance.objects.filter(
                    product=productinstance.product, size=productinstance.size, status=1
                ).first()
                if new_productinstance:
                    item.productinstance = new_productinstance
                    item.quantity = 1 if item.quantity == 0 else item.quantity
                else:
                    item.quantity = 0
            item.save()
        context['cart'] = cart
        context['cart_table'] = cart_items if cart_items else False
    except Cart.DoesNotExist:
        context['cart_table'] = False
    return context


def common_context(request):
    context = {}

    if not request.user.is_authenticated:
        context['unauthenticated'] = True
    else:
        # вкладки админки
        context = create_admin_pages(request, context)

        # содержание корзины
        context = create_cart_table(request, context)
    return context
