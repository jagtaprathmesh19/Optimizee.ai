# Create your views here.
from django.urls import path
from .views import (
    food_donation_form,
    food_donation_list,
    ngo_list,
    index,
    get_locations,
    generate_route,
)

urlpatterns = [
    path("donation_form", food_donation_form, name="food_donation_form"),
    path("food-donations/", food_donation_list, name="food_donations_list"),
    path("ngo_list", ngo_list, name="ngo_list"),
    path("route_optimize", index, name="index"),
    path("locations/", get_locations, name="locations"),
    path("route/", generate_route, name="generate_route"),
]
