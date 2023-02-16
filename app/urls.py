from django.urls import path

from .models import Item
from .views import ItemFilterView, ItemDetailView, ItemCreateView, ItemUpdateView, ItemDeleteView, MainFormView, MonthCalendar, LoginView, LogoutView, AboutView

# アプリケーションのルーティング設定

urlpatterns = [
    path('', MainFormView.as_view(), name='main'),
    path('month/', MonthCalendar.as_view(), name='month'),
    path('month/<int:year>/<int:month>/', MonthCalendar.as_view(), name='month'),
    path("login", LoginView.as_view(), name='login'),
    path("logout", LogoutView.as_view(), name='logout'),
    path("about", AboutView.as_view(), name='about')
]
