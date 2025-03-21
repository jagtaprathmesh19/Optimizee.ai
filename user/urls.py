from django.urls import path
from .views import (
    upload_image_and_voice,
    dashboard,
    recipe_slider,
    rotting_index,
    video_feed,
    community,
    detect,
    detected_objects,
    index,
    dashboard_data,
)

app_name = "user"

urlpatterns = [
    # Main pages
    path("index/", index, name="index"),
    path("", dashboard, name="dashboard"),
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard-data/", dashboard_data, name="dashboard-data"),
    path("community/", community, name="community"),
    # Food analysis features
    path("add/", upload_image_and_voice, name="upload_image_and_voice"),
    path("get_detections/", detected_objects, name="detected_objects"),
    path("recipe_slider/", recipe_slider, name="recipe_slider"),
    path("rotting_index/", rotting_index, name="rotting_index"),
    # Video and detection endpoints
    path("video_feed/", video_feed, name="video_feed"),
    path("food_detect/", detect, name="detect"),
    # path("video_feed1/", video_feed1, name="video_feed1"),
    # Testing
    # path("test/", test, name="test"),
]
