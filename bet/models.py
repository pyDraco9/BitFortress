from django.db import models
import django.utils.timezone as timezone


# Create your models here.
class BetClass(models.Model):
    name = models.CharField(verbose_name=u'竞猜分类', max_length=255)

    class Meta:
        verbose_name = u'M - 竞猜分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Bet(models.Model):
    title = models.CharField(verbose_name=u'标题', max_length=255)
    note = models.TextField(verbose_name=u'正文', blank=True)
    betClass = models.ForeignKey(BetClass, verbose_name=u'竞猜分类', blank=True, null=True)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    online_time = models.DateTimeField(verbose_name=u'上线时间', default=timezone.now)
    offline_time = models.DateTimeField(verbose_name=u'下线时间', default=timezone.now)
    option = models.BooleanField(verbose_name=u'开奖选项', default=False)
    status = models.BooleanField(verbose_name=u'开奖状态', default=False)
    settlement = models.BooleanField(verbose_name=u'已结算', default=False)

    class Meta:
        verbose_name = u'M - 竞猜列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class PaymentOption(models.Model):
    rpc_address = models.CharField(verbose_name=u'RPC地址', max_length=255)
    rpc_port = models.CharField(verbose_name=u'RPC端口', max_length=255)
    rpc_username = models.CharField(verbose_name=u'RPC用户', max_length=255)
    rpc_password = models.CharField(verbose_name=u'RPC密码', max_length=255)

    class Meta:
        verbose_name = u'M - RPC钱包设置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.rpc_address + ":" + self.rpc_port


class PaymentAddress(models.Model):
    address = models.CharField(verbose_name=u'钱包地址', max_length=34, unique=True)
    account = models.CharField(verbose_name=u'钱包账户', max_length=100)
    privkey = models.CharField(verbose_name=u'钱包私钥', max_length=256)

    class Meta:
        verbose_name = u'收款钱包地址'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.address


class PaymentBackAddress(models.Model):
    address = models.CharField(verbose_name=u'钱包地址', max_length=34, unique=True)

    class Meta:
        verbose_name = u'回款钱包地址'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.address


class BetLog(models.Model):
    bet = models.ForeignKey(Bet, verbose_name=u'竞猜ID', blank=True, null=True)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    option = models.BooleanField(verbose_name=u'YES', default=False)
    address = models.ForeignKey(PaymentAddress, verbose_name=u'收款地址')
    backAddress = models.ForeignKey(PaymentBackAddress, verbose_name=u'回款地址')

    class Meta:
        verbose_name = u'下注列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.address.address


class PaymentLog(models.Model):
    txid = models.CharField(verbose_name=u'txid', max_length=255, unique=True)
    amount = models.DecimalField(verbose_name=u'交易量', default=0, max_digits=16, decimal_places=8)
    address = models.ForeignKey(BetLog, verbose_name=u'地址')
    confirmations = models.IntegerField(verbose_name=u'确认次数', default=0)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        verbose_name = u'收款钱包日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.txid


class PaymentBackLog(models.Model):
    txid = models.CharField(verbose_name=u'txid', max_length=255, unique=True)
    amount = models.DecimalField(verbose_name=u'交易量', default=0, max_digits=16, decimal_places=8)
    fee = models.DecimalField(verbose_name=u'矿工费', default=0, max_digits=16, decimal_places=8)
    address = models.ForeignKey(PaymentBackAddress, verbose_name=u'地址')
    confirmations = models.IntegerField(verbose_name=u'确认次数', default=0)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        verbose_name = u'回款钱包日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.txid
