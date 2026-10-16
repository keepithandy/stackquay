from functools import partial

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from core import views

router = DefaultRouter()
router.register("records", views.RecordViewSet, basename="record")

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("health/live/", views.LiveView.as_view(), name="live"),
    path("health/ready/", views.ReadyView.as_view(), name="ready"),
    path("api/v1/auth/register/", views.RegisterView.as_view()),
    path("api/v1/auth/verify/", views.VerifyView.as_view()),
    path("api/v1/auth/resend-verification/", views.ResendVerificationView.as_view()),
    path("api/v1/auth/login/", views.LoginView.as_view()),
    path("api/v1/auth/logout/", views.LogoutView.as_view()),
    path("api/v1/auth/me/", views.MeView.as_view()),
    path("api/v1/auth/change-password/", views.ChangePasswordView.as_view()),
    path("api/v1/auth/password-reset/", views.PasswordResetView.as_view()),
    path("api/v1/auth/password-reset/confirm/", views.PasswordResetConfirmView.as_view()),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
    path("accounts/verify/<uid>/<token>/", views.verification_page),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/reset_done.html",
        ),
    ),
]
handler400 = partial(views.plain_error, status=400)
handler403 = partial(views.plain_error, status=403)
handler404 = partial(views.plain_error, status=404)
handler500 = partial(views.plain_error, status=500)
