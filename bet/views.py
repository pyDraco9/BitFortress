from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth, messages

from jsonrpc import json
from .models import *
from .forms import *
from django.utils.timezone import now
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import pyqrcode
import decimal


# Create your views here.
def index(request, p='1'):
    bets = Bet.objects.filter(online_time__lte=now()).order_by('-create_time')  # offline_time__gt=now()
    i = 0
    for bet in bets:
        betLog = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                       paymentlog__create_time__lte=bet.offline_time)
        betLogYSum = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                           paymentlog__create_time__lte=bet.offline_time,
                                           option=True).aggregate(Sum('paymentlog__amount'))
        betLogNSum = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                           paymentlog__create_time__lte=bet.offline_time,
                                           option=False).aggregate(Sum('paymentlog__amount'))
        if len(betLog) > 0:
            bets[i].log_count = betLog.count
        if 'paymentlog__amount__sum' in betLogYSum:
            if betLogYSum['paymentlog__amount__sum'] is not None:
                bets[i].betLogY_sum = betLogYSum['paymentlog__amount__sum']
            else:
                bets[i].betLogY_sum = 0
        else:
            bets[i].betLogY_sum = 0
        if 'paymentlog__amount__sum' in betLogNSum:
            if betLogNSum['paymentlog__amount__sum'] is not None:
                bets[i].betLogN_sum = betLogNSum['paymentlog__amount__sum']
            else:
                bets[i].betLogN_sum = 0
        else:
            bets[i].betLogN_sum = 0
        bets[i].betLogA_sum = bets[i].betLogY_sum + bets[i].betLogN_sum
        i += 1
    paginator = Paginator(bets, 10)
    try:
        bets = paginator.page(p)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        bets = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        bets = paginator.page(paginator.num_pages)
    c = {'page_tag': "index", 'bets': bets, 'now': now()}
    return render(request, 'index.html', c)


def view(request, bid='0'):
    bet = Bet.objects.filter(id=bid)
    if len(bet) > 0:
        bet = bet[0]
        paymentLog = PaymentLog.objects.filter(address__bet=bet, amount__gt=0, confirmations__gt=0,
                                               create_time__lte=bet.offline_time).order_by(
            '-create_time')
        betLogY = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                        paymentlog__create_time__lte=bet.offline_time,
                                        option=True)
        betLogN = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                        paymentlog__create_time__lte=bet.offline_time,
                                        option=False)
        betLogYSum = betLogY.aggregate(Sum('paymentlog__amount'))
        betLogNSum = betLogN.aggregate(Sum('paymentlog__amount'))
        if 'paymentlog__amount__sum' in betLogYSum:
            if betLogYSum['paymentlog__amount__sum'] is not None:
                betLogYSum = betLogYSum['paymentlog__amount__sum']
            else:
                betLogYSum = 0
        else:
            betLogYSum = 0
        if 'paymentlog__amount__sum' in betLogNSum:
            if betLogNSum["paymentlog__amount__sum"] is not None:
                betLogNSum = betLogNSum['paymentlog__amount__sum']
            else:
                betLogNSum = 0
        else:
            betLogNSum = 0
        betLogASum = betLogYSum + betLogNSum
        betLogRealSum = betLogASum / decimal.Decimal(100) * decimal.Decimal(98)
        if bet.option:
            betLogPrincipalSum = betLogYSum
        else:
            betLogPrincipalSum = betLogNSum
        betLogAssignedSum = betLogRealSum - betLogPrincipalSum
        i = 0
        for pl in paymentLog:
            paymentLog[i].payBackAmount = (
                decimal.Decimal(pl.amount) + decimal.Decimal(pl.amount) / decimal.Decimal(
                    betLogPrincipalSum) * decimal.Decimal(betLogAssignedSum)).quantize(
                decimal.Decimal('0.00000000'))
            i += 1
        c = {'page_tag': "view", 'bet': bet, 'now': now(), 'paymentLog': paymentLog, 'betLogY': betLogY,
             'betLogN': betLogN, 'betLogASum': betLogASum, 'betLogYSum': betLogYSum, 'betLogNSum': betLogNSum}
    else:
        messages.add_message(request, messages.ERROR, "该竞猜不存在")
        c = {'page_tag': "view", 'bet': bet, 'now': now()}
    return render(request, 'view.html', c)


@csrf_exempt
def vote(request, bid='0', v='0'):
    c = {'page_tag': "vote", 'now': now(), 'bid': bid, 'v': v}
    bet = Bet.objects.filter(id=bid)
    if len(bet) > 0:
        bet = bet[0]
        if v is not '0' and v is not '1':
            messages.add_message(request, messages.ERROR, "选项错误")
        else:
            if request.method == 'POST':
                post_address = request.POST['address'].strip()
                if post_address == '':
                    messages.add_message(request, messages.ERROR, "请输入地址")
                    return render(request, 'vote.html', c)
                    exit()
                paymentBackAddress = PaymentBackAddress.objects.filter(address=post_address)
                if len(paymentBackAddress) == 0:
                    paymentBackAddress = PaymentBackAddress.objects.create(address=post_address)
                else:
                    paymentBackAddress = paymentBackAddress[0]
                PaymentOptions = PaymentOption.objects.order_by('-id')
                if len(PaymentOptions) == 0:
                    return HttpResponse(json.dumps({'error': -402}))
                try:
                    rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (
                        PaymentOptions[0].rpc_username, PaymentOptions[0].rpc_password, PaymentOptions[0].rpc_address,
                        PaymentOptions[0].rpc_port))
                    address = rpc_connection.getnewaddress('Bet')
                    privkey = rpc_connection.dumpprivkey(address)
                    if address is not None and privkey is not None:
                        address = PaymentAddress.objects.create(address=address, account='Bet', privkey=privkey)
                        BetLog.objects.create(bet=bet, option=(v == '1'), address=address,
                                              backAddress=paymentBackAddress)
                        address_qrcode = pyqrcode.create(address.address)
                        c = {'page_tag': "vote", 'now': now(), 'bet': bet, 'bid': bid, 'v': v, 'address': address,
                             'address_qrcode': 'data:image/png;base64,' + address_qrcode.png_as_base64_str(scale=4)}
                    else:
                        return HttpResponse(json.dumps({'error': -404}))
                except Exception as ex:
                    print(ex)
                    return HttpResponse(json.dumps({'error': -403}))
    else:
        messages.add_message(request, messages.ERROR, "该竞猜不存在")

    return render(request, 'vote.html', c)


def api_tx(request, txid):
    PaymentOptions = PaymentOption.objects.order_by('-id')
    # if len(PaymentOptions) is 0:
    # return HttpResponse(json.dumps({'error': -401}))

    # try:
    rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (
        PaymentOptions[0].rpc_username, PaymentOptions[0].rpc_password, PaymentOptions[0].rpc_address,
        PaymentOptions[0].rpc_port))
    transaction = rpc_connection.gettransaction(txid)
    print(transaction)
    confirmations = transaction['confirmations']
    details = transaction['details']

    for detail in details:
        amount = detail['amount']
        address = detail['address']

        if detail['category'] == 'receive':
            betLog = BetLog.objects.filter(address__address=address)
            paymentLog = PaymentLog.objects.filter(txid=txid)
            if len(paymentLog) > 0:
                paymentLog[0].confirmations = confirmations
                paymentLog[0].save()
            else:
                PaymentLog.objects.create(txid=txid, amount=decimal.Decimal(amount),
                                          address=betLog[0],
                                          confirmations=confirmations)
        if detail['category'] == 'send':
            betLog = BetLog.objects.filter(backAddress__address=address)
            if len(betLog) > 0:
                paymentBackLog = PaymentBackLog.objects.filter(txid=txid)
                if len(paymentBackLog) > 0:
                    paymentBackLog[0].confirmations = confirmations
                    paymentBackLog[0].save()
                else:
                    PaymentBackLog.objects.create(txid=txid,
                                                  amount=decimal.Decimal(amount),
                                                  fee=decimal.Decimal(detail['fee']),
                                                  address=betLog[0].backAddress, confirmations=confirmations)


                    # except Exception as ex:

    # print(ex)
    #    return HttpResponse(json.dumps({'error': -400}))

    return HttpResponse(json.dumps(transaction, default=decimal_default), content_type="application/json")


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


@csrf_exempt
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if username == '' or password == '':
            messages.add_message(request, messages.WARNING, '帐号密码不能为空.')
        else:
            user = auth.authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect("/dashwood/dashboard/")
            else:
                if user is None:
                    messages.add_message(request, messages.ERROR, '帐号密码错误.')
                elif not user.is_active:
                    messages.add_message(request, messages.ERROR, '帐号已被封禁.')
    return render(request, 'admin_login.html')


@csrf_exempt
def admin_logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


@csrf_exempt
def admin_list(request, p='1', bid='0', v=None):
    if not request.user.is_active:
        return HttpResponseRedirect("/")
    if bid is not '0' and v is not None:
        bet = Bet.objects.filter(id=bid)
        if len(bet) > 0:
            bet = bet[0]
            if v == '0':
                if bet.status is True and bet.option is False:
                    bet.status = False
                else:
                    bet.option = False
                    bet.status = True
            elif v == '1':
                if bet.status is True and bet.option is True:
                    bet.status = False
                else:
                    bet.option = True
                    bet.status = True
            elif v == '2':
                bet.settlement = True
                bet.save()
                if bet.option == '0':
                    print('settlement 0')
                elif bet.option == '1':
                    print('settlement 0')
            else:
                messages.add_message(request, messages.ERROR, "选项错误")
            bet.save()
            return HttpResponseRedirect("/dashwood/list/" + p + "/")
        else:
            messages.add_message(request, messages.ERROR, "该竞猜不存在")
    bets = Bet.objects.filter().order_by('-id')
    paginator = Paginator(bets, 50)
    try:
        bets = paginator.page(p)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        bets = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        bets = paginator.page(paginator.num_pages)
    c = {'p': p, 'bets': bets}
    return render(request, 'admin_list.html', c)


@csrf_exempt
def admin_lot(request, bid='0', confirm='0'):
    bet = Bet.objects.filter(id=bid)
    if len(bet) > 0:
        bet = bet[0]
        paymentLog = PaymentLog.objects.filter(address__bet=bet, amount__gt=0, confirmations__gt=0,
                                               create_time__lte=bet.offline_time,
                                               address__option=bet.option).order_by('-create_time')
        betLogY = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                        paymentlog__create_time__lte=bet.offline_time,
                                        option=True)
        betLogN = BetLog.objects.filter(bet_id=bet, paymentlog__amount__gt=0, paymentlog__confirmations__gt=0,
                                        paymentlog__create_time__lte=bet.offline_time,
                                        option=False)
        betLogYSum = betLogY.aggregate(Sum('paymentlog__amount'))
        betLogNSum = betLogN.aggregate(Sum('paymentlog__amount'))

        if 'paymentlog__amount__sum' in betLogYSum:
            if betLogYSum['paymentlog__amount__sum'] is not None:
                betLogYSum = betLogYSum['paymentlog__amount__sum']
            else:
                betLogYSum = 0
        else:
            betLogYSum = 0
        if 'paymentlog__amount__sum' in betLogNSum:
            if betLogNSum["paymentlog__amount__sum"] is not None:
                betLogNSum = betLogNSum['paymentlog__amount__sum']
            else:
                betLogNSum = 0
        else:
            betLogNSum = 0
        betLogASum = betLogYSum + betLogNSum
        betLogRealSum = betLogASum / decimal.Decimal(100) * decimal.Decimal(98)
        if bet.option:
            betLogPrincipalSum = betLogYSum
        else:
            betLogPrincipalSum = betLogNSum
        betLogAssignedSum = betLogRealSum - betLogPrincipalSum

        PaymentOptions = PaymentOption.objects.order_by('-id')
        if len(PaymentOptions) == 0:
            return HttpResponse(json.dumps({'error': -401}))
        try:
            rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (
                PaymentOptions[0].rpc_username, PaymentOptions[0].rpc_password,
                PaymentOptions[0].rpc_address,
                PaymentOptions[0].rpc_port))
            i = 0
            betSettlement = bet.settlement

            if confirm == '1' and len(paymentLog) == 0 and betSettlement is False:
                bet.settlement = True
                bet.save()
            else:
                for pl in paymentLog:
                    paymentLog[i].payBackAmount = (
                        decimal.Decimal(pl.amount) + decimal.Decimal(pl.amount) / decimal.Decimal(
                            betLogPrincipalSum) * decimal.Decimal(betLogAssignedSum)).quantize(
                        decimal.Decimal('0.00000000'))
                    if confirm == '1' and betSettlement is False:
                        print(u'发放奖金')
                        print(paymentLog[i].payBackAmount)
                        print('to')
                        if paymentLog[i].address.backAddress is not None:
                            backAddress = paymentLog[i].address.backAddress.address
                        else:
                            backAddress = paymentLog[i].address.address.address

                        print(backAddress)
                        print('--------')
                        rpc_connection.sendtoaddress(backAddress, paymentLog[i].payBackAmount)
                        if betSettlement is False:
                            bet.settlement = True
                            bet.save()

                i += 1

        except Exception as ex:
            print(ex)
            return HttpResponse(json.dumps({'error': -403}))
        c = {'page_tag': "view", 'bet': bet, 'now': now(), 'paymentLog': paymentLog, 'betLogY': betLogY,
             'betLogN': betLogN, 'betLogASum': betLogASum, 'betLogYSum': betLogYSum, 'betLogNSum': betLogNSum,
             'betLogRealSum': betLogRealSum, 'betLogPrincipalSum': betLogPrincipalSum,
             'betLogAssignedSum': betLogAssignedSum}
    else:
        messages.add_message(request, messages.ERROR, "该竞猜不存在")
        c = {'page_tag': "view", 'bet': bet, 'now': now()}
    return render(request, 'admin_lot.html', c)


@csrf_exempt
def admin_dashboard(request):
    if not request.user.is_active:
        return HttpResponseRedirect("/")
    payout = PaymentBackLog.objects.all().aggregate(Sum('amount'))
    payoutfee = PaymentBackLog.objects.all().aggregate(Sum('fee'))
    payin = PaymentLog.objects.all().aggregate(Sum('amount'))
    ingame = PaymentLog.objects.filter(address__bet__settlement=False).aggregate(Sum('amount'))

    payout = (payout['amount__sum'] is not None) and -payout['amount__sum'] or 0
    payoutfee = (payoutfee['fee__sum'] is not None) and -payoutfee['fee__sum'] or 0
    payin = (payin['amount__sum'] is not None) and payin['amount__sum'] or 0
    ingame = (ingame['amount__sum'] is not None) and ingame['amount__sum'] or 0

    PaymentOptions = PaymentOption.objects.order_by('-id')
    if len(PaymentOptions) == 0:
        return HttpResponse(json.dumps({'error': -401}))

    try:
        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (
            PaymentOptions[0].rpc_username, PaymentOptions[0].rpc_password,
            PaymentOptions[0].rpc_address,
            PaymentOptions[0].rpc_port))
        wallet_balance = rpc_connection.getbalance()

    except Exception as ex:
        print(ex)
        return HttpResponse(json.dumps({'error': -403}))

    freemoney = payin - ingame - payout - payoutfee
    c = {'payout': payout, 'payoutfee': payoutfee, 'payin': payin, 'ingame': ingame, 'freemoney': freemoney,
         'wallet_balance': wallet_balance}
    return render(request, 'admin_dashboard.html', c)
