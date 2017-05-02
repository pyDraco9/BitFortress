from django.contrib import admin
from django.forms import TextInput

from .models import *


# Register your models here.
class BetClassAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(BetClass, BetClassAdmin)


class BetAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '200'})},
    }
    list_display = ('title', 'note', 'betClass', 'status', 'option', 'settlement')
    search_fields = ['title']


admin.site.register(Bet, BetAdmin)


class BetLogAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '200'})},
    }
    list_display = ('bet', 'create_time', 'option', 'address', 'backAddress')
    search_fields = ['bet', 'create_time', 'address', 'backAddress']


admin.site.register(BetLog, BetLogAdmin)


class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ('rpc_address', 'rpc_port', 'rpc_username', 'rpc_password')


admin.site.register(PaymentOption, PaymentOptionAdmin)


class PaymentLogAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '200'})},
    }
    list_display = ('txid', 'address', 'amount', 'confirmations', 'create_time', 'update_time')
    search_fields = ['txid', 'amount', 'address']


admin.site.register(PaymentLog, PaymentLogAdmin)


class PaymentBackLogAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '200'})},
    }
    list_display = ('txid', 'address', 'amount', 'fee', 'confirmations', 'create_time', 'update_time')
    search_fields = ['txid', 'amount', 'address']


admin.site.register(PaymentBackLog, PaymentBackLogAdmin)


class PaymentAddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'account', 'privkey')
    search_fields = ['address', 'account', 'privkey']


admin.site.register(PaymentAddress, PaymentAddressAdmin)


class PaymentBackAddressAdmin(admin.ModelAdmin):
    search_fields = ['address']


admin.site.register(PaymentBackAddress, PaymentBackAddressAdmin)
