from django.contrib import admin
from models import Consumer, Supplier, TransportTable, TransportRoute


admin.site.register(Consumer)
admin.site.register(Supplier)
admin.site.register(TransportTable)
admin.site.register(TransportRoute)
