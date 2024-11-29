from django.db import models
from django.core.validators import MinValueValidator


class Consumer(models.Model):
    good_need = models.IntegerField(validators=[MinValueValidator(1)])


class Supplier(models.Model):
    good_amount = models.IntegerField(validators=[MinValueValidator(1)])


class TransportTable(models.Model):
    pass


class TransportRoute(models.Model):
    price = models.IntegerField(validators=[MinValueValidator(0)])
    goods = models.IntegerField(validators=[MinValueValidator(0)])
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='transport_routes')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='transport_routes')
    transport_table = models.ForeignKey(TransportTable, on_delete=models.CASCADE, related_name='transport_routs')
