from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django_filters.views import FilterView
from django.views.generic.base import TemplateView
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from .filters import ItemFilterSet
from .forms import ItemForm, MainForm, LoginForm
from .models import Item, Stamping

from .mixins import MonthCalendarMixin, MonthWithScheduleMixin

# 未ログインのユーザーにアクセスを許可する場合は、LoginRequiredMixinを継承から外してください。
#
# LoginRequiredMixin：未ログインのユーザーをログイン画面に誘導するMixin
# 参考：https://docs.djangoproject.com/ja/2.1/topics/auth/default/#the-loginrequired-mixin

class ItemFilterView(LoginRequiredMixin, FilterView):
    """
    ビュー：一覧表示画面

    以下のパッケージを使用
    ・django-filter 一覧画面(ListView)に検索機能を追加
    https://django-filter.readthedocs.io/en/master/
    """
    model = Item

    # django-filter 設定
    filterset_class = ItemFilterSet
    # django-filter ver2.0対応 クエリ未設定時に全件表示する設定
    strict = False

    # 1ページの表示
    paginate_by = 10

    def get(self, request, **kwargs):
        """
        リクエスト受付
        セッション変数の管理:一覧画面と詳細画面間の移動時に検索条件が維持されるようにする。
        """

        # 一覧画面内の遷移(GETクエリがある)ならクエリを保存する
        if request.GET:
            request.session['query'] = request.GET
        # 詳細画面・登録画面からの遷移(GETクエリはない)ならクエリを復元する
        else:
            request.GET = request.GET.copy()
            if 'query' in request.session.keys():
                for key in request.session['query'].keys():
                    request.GET[key] = request.session['query'][key]

        return super().get(request, **kwargs)

    def get_queryset(self):
        """
        ソート順・デフォルトの絞り込みを指定
        """
        # デフォルトの並び順として、登録時間（降順）をセットする。
        return Item.objects.all().order_by('-created_at')

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        表示データの設定
        """
        # 表示データを追加したい場合は、ここでキーを追加しテンプレート上で表示する
        # 例：kwargs['sample'] = 'sample'
        return super().get_context_data(object_list=object_list, **kwargs)


class ItemDetailView(LoginRequiredMixin, DetailView):
    """
    ビュー：詳細画面
    """
    model = Item

    def get_context_data(self, **kwargs):
        """
        表示データの設定
        """
        # 表示データの追加はここで 例：
        # kwargs['sample'] = 'sample'
        return super().get_context_data(**kwargs)


class ItemCreateView(LoginRequiredMixin, CreateView):
    """
    ビュー：登録画面
    """
    model = Item
    form_class = ItemForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        """
        登録処理
        """
        item = form.save(commit=False)
        item.created_by = self.request.user
        item.created_at = timezone.now()
        item.updated_by = self.request.user
        item.updated_at = timezone.now()
        item.save()

        return HttpResponseRedirect(self.success_url)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """
    ビュー：更新画面
    """
    model = Item
    form_class = ItemForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        """
        更新処理
        """
        item = form.save(commit=False)
        item.updated_by = self.request.user
        item.updated_at = timezone.now()
        item.save()

        return HttpResponseRedirect(self.success_url)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    """
    ビュー：削除画面
    """
    model = Item
    success_url = reverse_lazy('index')

    def delete(self, request, *args, **kwargs):
        """
        削除処理
        """
        item = self.get_object()
        item.delete()

        return HttpResponseRedirect(self.success_url)

class LoginView(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = "app/login.html"
    success_url = reverse_lazy('main')

class LogoutView(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = "account/login.html"

class MainFormView(LoginRequiredMixin, CreateView):
    template_name = 'app/main.html'
    form_class = MainForm
    success_url = reverse_lazy('main')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # はじめに継承元のメソッドを呼び出す
        today = localtime(timezone.now()).date()
        context['today'] = today
        attends = Stamping.objects.filter(stamping_by = self.request.user, stamping_type = 0,stamping__date=today).order_by('stamping')
        leaves = Stamping.objects.filter(stamping_by = self.request.user, stamping_type = 1,stamping__date=today).order_by('stamping').reverse()
        if attends.exists():
            context["attend"] = attends[0].stamping
        if leaves.exists():
            context["leave"] = leaves[0].stamping
        return context

    def form_valid(self, form):
        item = form.save(commit=False)
        item.stamping_by = self.request.user
        item.stamping = localtime(timezone.now())
        if 'attend' in self.request.POST:
            item.stamping_type = 0
            messages.success(self.request, '出勤打刻をしました。')
        elif 'leave' in self.request.POST:
            item.stamping_type = 1
            messages.success(self.request, '退勤打刻をしました。')
        item.save()
        
        return HttpResponseRedirect(self.success_url)

class MonthCalendar(LoginRequiredMixin, MonthWithScheduleMixin, TemplateView):
    """月間カレンダーを表示するビュー"""
    template_name = 'app/month.html'
    model = Stamping
    date_field = 'stamping'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_month_calendar()
        context.update(calendar_context)
        return context

class AboutView(TemplateView):
    template_name = 'app/about.html'