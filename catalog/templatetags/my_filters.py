from django.template.defaultfilters import register


@register.filter
def batch(lst, size):
    """
    Функция разделяет список lst на список списков по size элементов в каждом
    """
    n = len(lst)
    rows = n // size
    if n % size:
        rows += 1
    return [lst[i:i+size] for i in range(0, n, size)]


@register.filter
def price_format(numb):
    """
    Функция возвращает число с двумя цифрами после запятой
    """
    n = "{:.2f}".format(numb)
    return n


@register.filter
def product_count(count):
    """
    Функция возвращает строку с количеством товаров
    """
    r = f'{count} товаров' if count in range(11, 20) else None
    for k, v in {(1, ): 'товар', (2, 3, 4): 'товара', (0, 5, 6, 7, 8, 9): 'товаров'}.items():
        if not r and int(str(count)[-1]) in k:
            r = f'{count} {v}'
    return r


@register.simple_tag(takes_context=True)
def smart_url(context, **kwargs):
    """
    Функция генерирует ссылку на другую страницу с учетом примененных фильтров на текущей
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()
