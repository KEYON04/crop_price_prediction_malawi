from django.urls import path
from . import views

urlpatterns = [
    # Web UI Dashboard
    path("", views.dashboard_view, name="dashboard"),
    
    # REST API Endpoints
    path("api/districts/", views.api_districts, name="api_districts"),
    path("api/commodities/", views.api_commodities, name="api_commodities"),
    path("api/predictions/", views.api_predictions, name="api_predictions"),
    path("api/decisions/", views.api_decisions, name="api_decisions"),
    path("api/arbitrage/", views.api_arbitrage, name="api_arbitrage"),
    path("api/arbitrage/top/", views.api_top_arbitrage, name="api_top_arbitrage"),
    
    # User Authentication & Market Report Subscriptions
    path("api/auth/signup/", views.api_auth_signup, name="api_auth_signup"),
    path("api/auth/signin/", views.api_auth_signin, name="api_auth_signin"),
    path("api/auth/forgot-pin/", views.api_auth_forgot_pin, name="api_auth_forgot_pin"),
    path("api/auth/reset-pin/", views.api_auth_reset_pin, name="api_auth_reset_pin"),
    path("api/auth/me/", views.api_auth_me, name="api_auth_me"),
    path("api/auth/signout/", views.api_auth_signout, name="api_auth_signout"),
    path("api/reports/send/", views.api_send_market_report, name="api_send_market_report"),
]

