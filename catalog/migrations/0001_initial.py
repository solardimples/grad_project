# Generated by Django 4.2 on 2023-05-12 16:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
                ('description', models.TextField(blank=True, max_length=1000, null=True, verbose_name='Описание')),
                ('image', models.ImageField(blank=True, null=True, upload_to='static/images/brand_logos', verbose_name='Изображение')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'бренд',
                'verbose_name_plural': 'бренды',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'категория',
                'verbose_name_plural': 'категории',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Gender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'пол',
                'verbose_name_plural': 'пол',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Guest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guest_code', models.CharField(max_length=100, verbose_name='Идентификационный код гостя')),
                ('last_activity', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=50, verbose_name='Номер инвойса')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Дата инвойса')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'инвойс',
                'verbose_name_plural': 'инвойсы',
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('description', models.TextField(max_length=1000, verbose_name='Описание')),
                ('price', models.FloatField(verbose_name='Цена')),
                ('image', models.ImageField(upload_to='static/images/product_photos', verbose_name='Изображение')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.brand', verbose_name='Бренд')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.category', verbose_name='Категория')),
                ('gender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.gender', verbose_name='Пол')),
            ],
            options={
                'verbose_name': 'товар',
                'verbose_name_plural': 'товары',
                'ordering': ['date_updated'],
            },
        ),
        migrations.CreateModel(
            name='ProductInstanceStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'статус экземпляра товара',
                'verbose_name_plural': 'статусы экземпляров товаров',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'размер',
                'verbose_name_plural': 'размеры',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('purchase_price', models.FloatField(verbose_name='Цена закупки')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.invoice', verbose_name='Инвойс')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.product', verbose_name='Товар')),
                ('size', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.size', verbose_name='Размер')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.productinstancestatus', verbose_name='Статус')),
            ],
            options={
                'verbose_name': 'экземпляр товара',
                'verbose_name_plural': 'экземпляры товаров',
            },
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.guest')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]