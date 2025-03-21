from django.urls import path
from .views import generate_map, calculate, cart, spline

urlpatterns = [
    path("generate_map/", generate_map, name="generate_map"),
    path("calculate/", calculate, name="calculate"),
    path("cart/", cart, name="cart"),
    path("spline/", spline, name="spline"),
]
