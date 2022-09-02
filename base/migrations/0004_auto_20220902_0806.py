# Generated by Django 3.2 on 2022-09-02 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20220831_1752'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Orders'},
        ),
        migrations.RemoveField(
            model_name='order',
            name='products',
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('1', 'Pending'), ('2', 'Processed'), ('3', 'Delivered')], default='1', max_length=10, verbose_name='Order status'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='address'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='first_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='last_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='last name'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='mobile_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='mobile number'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='post_address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='post address'),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True, verbose_name='total order price'),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='description'),
        ),
    ]