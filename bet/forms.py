from django import forms

# place form definition here
from django import forms

choices = (
    ('1', u"发送奖金到付款地址，请注意，BitStamp, Coinbase, etc等部分钱包的发送地址是无法收款的，可能导致你无法领取到奖金。"),
    ('2', u"发送奖金到："),
)


class voteForm(forms.Form):
    option = forms.ChoiceField(label=u'', choices=choices,
                               widget=forms.RadioSelect(attrs={'class': 'custom-radio'}))
    address = forms.CharField(label=u'地址', min_length=34, max_length=34)
