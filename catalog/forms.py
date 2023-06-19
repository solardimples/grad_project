import re
from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from .models import *


# first_name, last_name, phone_number, city, delivery_method, address, payment_method, comment
class OrderDetails(forms.Form):

    full_name = forms.CharField(label='ФИО', required=True, min_length=3, max_length=50, widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Фамилия Имя Отчество'}))

    phone_number = forms.CharField(label='Телефон', required=True, widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'placeholder': '+375 (XX) XXX-XX-XX'}))

    city = forms.CharField(label='Город', min_length=3, max_length=50, required=True, widget=forms.widgets.TextInput(
        attrs={'class': 'form-control'}))

    choices = ((0, 'Выберите способ доставки...'), (1, 'Курьерская доставка'))
    delivery_method = forms.ChoiceField(label='Способ доставки', choices=choices, required=True,
                                        widget=forms.Select(attrs={'class': 'form-control'}))

    delivery_address = forms.CharField(label='Адрес доставки', min_length=3, max_length=10, required=True,
                                       widget=forms.widgets.TextInput(attrs={'class': 'form-control'}))

    choices = ((0, 'Выберите способ оплаты...'), (1, 'Картой онлайн'), (2, 'Картой курьеру'), (3, 'Наличными'))
    payment_method = forms.ChoiceField(label='Способ оплаты', choices=choices, required=True,
                                       widget=forms.Select(attrs={'class': 'form-control'}))

    comment = forms.CharField(label='Комментарий', max_length=1000, required=False, widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder': 'Ваш комментарий к заказу'}))

    error_css_class = 'error'

    def invalidate_field(self, field: str, error: str or forms.ValidationError, errors: dict):
        self.fields[field].widget.attrs.update({'class': 'form-control is-invalid'})
        errors.update(forms.ValidationError({field: error}))

    def clean(self):
        cleaned_data = super(OrderDetails, self).clean()
        delivery_method = cleaned_data.get('delivery_method')
        payment_method = cleaned_data.get('payment_method')

        errors = {}

        if delivery_method == '0':
            self.invalidate_field('delivery_method', 'Вам нужно выбрать способ доставки', errors)

        if payment_method == '0':
            self.invalidate_field('payment_method', 'Вам нужно выбрать способ оплаты', errors)

        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data


# Форма аутентификации пользователей
class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=10, widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'username', 'autofocus': True}))
    password = forms.CharField(label='Пароль', widget=forms.widgets.PasswordInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'password',
               'autocomplete': 'current-password'}))

    error_css_class = 'error'

    def invalidate_field(self, field, error):
        self.fields[field].widget.attrs.update({'class': 'form-control is-invalid'})
        raise forms.ValidationError({field: error})

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                self.invalidate_field('password', 'Неправильный пароль.')
        except User.DoesNotExist:
            self.invalidate_field('username', 'Пользователь не найден.')
        return cleaned_data


# Форма регистрации пользователей
class RegisterForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=10, min_length=4, widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'username'}))
    email = forms.EmailField(label='Почтовый ящик', required=True, widget=forms.widgets.EmailInput(
        attrs={'class': 'form-control', 'type': 'email', 'id': 'floatingInput', 'placeholder': 'name@example.com'}))
    password1 = forms.CharField(label='Пароль', widget=forms.widgets.PasswordInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'password',
               'autocomplete': 'new-password'}), strip=False)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.widgets.PasswordInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'password',
               'autocomplete': 'new-password'}), strip=False)

    error_css_class = 'error'

    def invalidate_field(self, field: str, error: str or forms.ValidationError, errors: dict):
        self.fields[field].widget.attrs.update({'class': 'form-control is-invalid'})
        errors.update(forms.ValidationError({field: error}))

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        username = cleaned_data.get('username',)
        email = cleaned_data.get('email')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        errors = {}

        # валидация логина
        if User.objects.filter(username=username):
            self.invalidate_field('username', 'Пользователь с таким именем уже существует.', errors)
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            self.invalidate_field('username', 'Логин может содержать только цифры и буквы латинского алфавита.', errors)
        if username.isdigit():
            self.invalidate_field('username', 'Логин не может состоять только из цифр.', errors)
        # валидация почты
        if User.objects.filter(email=email):
            self.invalidate_field('email', 'Данный почтовый ящик уже используется.', errors)
        # валидация пароля
        try:
            validate_password(password1)
            if password1 and password2 and password1 != password2:
                self.invalidate_field('password1', 'Пароли не совпадают.', errors)
                self.invalidate_field('password2', 'Пароли не совпадают.', errors)
        except forms.ValidationError as error:
            self.invalidate_field('password1', error, errors)

        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data


# Форма инициации сброса пароля на основе родительской формы django
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Почтовый ящик', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'type': 'email', 'id': 'floatingInput', 'placeholder': 'name@example.com',
               'aria-label': 'Email Address'}))

    error_css_class = 'error'

    class Meta:
        model = User
        fields = ('email', )

    def invalidate_field(self, field, error):
        self.fields[field].widget.attrs.update({'class': 'form-control is-invalid'})
        raise forms.ValidationError({field: error})

    def clean(self):
        cleaned_data = super(CustomPasswordResetForm, self).clean()
        email = cleaned_data.get('email')
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            self.invalidate_field('email', 'Аккаунт не найден')


# Форма сброса пароля на основе родительской формы django
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'new_password1'}))
    new_password2 = forms.CharField(label='Подтверждение нового пароля', widget=forms.widgets.TextInput(
        attrs={'class': 'form-control', 'id': 'floatingInput', 'placeholder': 'new_password2'}))

    error_css_class = 'error'

    class Meta:
        model = User
        fields = ('new_password1', 'new_password2')

    def invalidate_field(self, field: str, error: str or forms.ValidationError, errors: dict):
        self.fields[field].widget.attrs.update({'class': 'form-control is-invalid'})
        errors.update(forms.ValidationError({field: error}))

    def clean(self):
        cleaned_data = super(CustomSetPasswordForm, self).clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        errors = {}

        try:
            validate_password(new_password1)
            if new_password1 and not new_password2:
                self.invalidate_field('new_password1', 'Пароли не совпадают.', errors)
                self.invalidate_field('new_password2', 'Пароли не совпадают.', errors)
        except forms.ValidationError as error:
            self.invalidate_field('new_password1', error, errors)

        if errors:
            raise forms.ValidationError(errors)


# Форма фильтрации товаров на страницах каталога
class ProductFilterForm(forms.Form):
    gender = forms.MultipleChoiceField(
        label='Пол', choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input', 'type': 'checkbox'}), required=False)
    brand = forms.MultipleChoiceField(
        label='Бренд', choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input', 'type': 'checkbox'}), required=False)

    def __init__(self, selected_gender=None, selected_brand=None, selected_pks=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if selected_gender:
            self.fields['gender'].initial = selected_gender
        if selected_brand:
            self.fields['brand'].initial = selected_brand

        if selected_pks:
            queryset = Product.objects.filter(pk__in=selected_pks)
            gender_objects = Gender.objects.filter(product__in=queryset).distinct()
            brand_objects = Brand.objects.filter(product__in=queryset).distinct()

            self.fields['gender'].choices = [(i.id, i.name) for i in gender_objects]
            self.fields['brand'].choices = [(i.id, i.name) for i in brand_objects]


# Форма генерации доступных размеров товара для его страницы
class ProductCartForm(forms.Form):
    SIZE_ORDER = {'XS': 1, 'S': 2, 'M': 3, 'L': 4, 'XL': 5}

    size = forms.ChoiceField(choices=[], widget=forms.RadioSelect(
        attrs={'class': 'form-check-input', 'type': 'radio'}
    ), required=True)

    def __init__(self, instance_objects=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if instance_objects:
            size_objects = Size.objects.filter(productinstance__in=instance_objects.distinct()).distinct()
            if size_objects:
                choices = [(i.id, i.name) for i in size_objects]
                if all(isinstance(choice[1], int) for choice in choices):
                    sorted_choices = sorted(choices, key=lambda x: int(x[1]))
                else:
                    sorted_choices = sorted(choices, key=lambda x: self.SIZE_ORDER.get(x[1], 999))
                self.fields['size'].choices = sorted_choices
            else:
                self.fields['size'].required = False


class ReviewForm(forms.Form):
    text = forms.CharField(label='Текст', max_length=1000, required=True, widget=forms.Textarea(
        attrs={'class': 'form-control'}))

    choices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5))
    rating = forms.ChoiceField(label='Рейтинг', choices=choices, required=True, widget=forms.RadioSelect(
        attrs={'class': 'form-check-input', 'type': 'radio', 'name': 'rating'}
    ))
