from django.urls import include, path

from dashboard import views_ext
from dashboard.views import (
    ShareCreateView,
    ShareDeleteView,
    ShareDetailView,
    ShareListView,
    ShareUpdateView,
)

app_name = "dashboard"

urlpatterns = [
    path("", ShareListView.as_view(), name="index"),
    path("create", ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", ShareDeleteView.as_view(), name="delete"),
    path("watchlist/", views_ext.watchlist_list, name="watchlist"),
    path("watchlist/add/", views_ext.watchlist_add, name="watchlist_add"),
    path("watchlist/remove/<int:pk>/", views_ext.watchlist_remove, name="watchlist_remove"),
    path("alerts/", views_ext.alerts_list, name="alerts"),
    path("alerts/add/", views_ext.alert_add, name="alert_add"),
    path("alerts/remove/<int:pk>/", views_ext.alert_remove, name="alert_remove"),
    path("<int:pk>", ShareDetailView.as_view(), name="detail"),
    path("api/", include("dashboard.api.urls")),
]
