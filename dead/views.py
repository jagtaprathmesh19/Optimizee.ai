import os
import logging

from django.shortcuts import render
from django import forms
from django.http import JsonResponse
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from user.models import FoodItem, FoodItemPurchase

from statistics import mean
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import osmnx as ox
import googlemaps
from shapely.geometry import Point
from geopy.distance import geodesic


logger = logging.getLogger(__name__)

# Initialize the Google Maps client
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))


def get_street_network(area):
    return ox.graph_from_place(area, network_type="walk")


def load_sample_food_banks():
    data = {
        "name": [
            "Food Bank For New York City",
            "City Harvest",
            "New York Common Pantry",
            "Holy Apostles Soup Kitchen",
            "St. John's Bread & Life",
            "Part of the Solution (POTS)",
            "Bowery Mission",
            "Food Bank of Lower Fairfield County",
            "Hope Community Services",
            "Feeding Westchester",
        ],
        "address": [
            "39 Broadway, New York, NY 10006",
            "6 East 32nd Street, New York, NY 10016",
            "8 East 109th Street, New York, NY 10029",
            "296 9th Avenue, New York, NY 10001",
            "795 Lexington Ave, Brooklyn, NY 11221",
            "2759 Webster Avenue, Bronx, NY 10458",
            "227 Bowery, New York, NY 10002",
            "461 Glenbrook Road, Stamford, CT 06906",
            "50 Washington Avenue, New Rochelle, NY 10801",
            "200 Clearbrook Road, Elmsford, NY 10523",
        ],
        "phone": [
            "(212) 566-7855",
            "(646) 412-0600",
            "(917) 720-9700",
            "(212) 924-0167",
            "(718) 574-0058",
            "(718) 220-4892",
            "(212) 674-3456",
            "(203) 358-8898",
            "(914) 636-4010",
            "(914) 923-1100",
        ],
        "hours": [
            "Mon-Fri 9AM-5PM",
            "Mon-Fri 8AM-6PM",
            "Mon-Sat 9AM-5PM",
            "Mon-Fri 10:30AM-1:30PM",
            "Mon-Fri 8AM-4PM",
            "Mon-Sat 9:30AM-3:30PM",
            "Mon-Sat 8AM-6PM",
            "Mon-Fri 8AM-4PM",
            "Mon-Fri 9AM-5PM",
            "Mon-Fri 8AM-5PM",
        ],
        "needs": [
            "Canned goods, rice, pasta",
            "Fresh produce, canned goods",
            "Non-perishable foods",
            "Canned foods, dry goods",
            "Canned goods, baby food",
            "Non-perishable items",
            "Canned goods, hygiene items",
            "Non-perishable foods",
            "Canned goods, pasta",
            "Fresh produce, canned goods",
        ],
    }
    return pd.DataFrame(data)


def geocode_address(address):
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return location["lat"], location["lng"]
        return None
    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}")
        return None


def get_route(G, origin_coords, dest_coords):
    try:
        orig_node = ox.nearest_nodes(G, X=origin_coords[1], Y=origin_coords[0])
        dest_node = ox.nearest_nodes(G, X=dest_coords[1], Y=dest_coords[0])
        route = ox.shortest_path(G, orig_node, dest_node, weight="length")
        route_coords = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in route]
        route_length = ox.shortest_path_length(G, orig_node, dest_node, weight="length")
        return {"coords": route_coords, "distance": route_length, "path": route}
    except Exception as e:
        logger.error(f"Error calculating route: {str(e)}")
        return None


def create_geopandas_df(df):
    geometries = []
    coordinates = []
    for address in df["address"]:
        coords = geocode_address(address)
        if coords:
            geometries.append(Point(coords[1], coords[0]))
            coordinates.append(coords)
        else:
            geometries.append(None)
            coordinates.append(None)
    gdf = gpd.GeoDataFrame(df, geometry=geometries)
    gdf["coordinates"] = coordinates
    return gdf.dropna(subset=["geometry"])


def create_map(gdf, user_location=None, max_distance=None, route_details=None):
    if user_location:
        center = user_location
    else:
        center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]

    m = folium.Map(location=center, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in gdf.iterrows():
        if row.geometry:
            distance_text = ""
            if user_location:
                distance = calculate_distance(
                    user_location, (row.geometry.y, row.geometry.x)
                )
                if max_distance and distance > max_distance:
                    continue
                distance_text = f"<br>Distance: {distance:.1f} km"

            popup_content = f"""
                <b>{row["name"]}</b><br>
                Address: {row["address"]}<br>
                Phone: {row["phone"]}<br>
                Hours: {row["hours"]}<br>
                Needs: {row["needs"]}{distance_text}
            """

            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(marker_cluster)

    if user_location:
        folium.Marker(
            location=user_location,
            popup="Your Location",
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(m)

    if route_details:
        folium.PolyLine(
            locations=route_details["coords"], weight=4, color="blue", opacity=0.5
        ).add_to(m)

    return m


def calculate_distance(point1, point2):
    return geodesic(point1, point2).kilometers


class LocationForm(forms.Form):
    user_address = forms.CharField(label="Enter your address:", required=True)
    max_distance = forms.IntegerField(
        label="Maximum distance (km):", min_value=1, max_value=20, initial=5
    )
    selected_food_bank = forms.ChoiceField(
        label="Select a food bank to get directions:", required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        df = load_sample_food_banks()
        gdf = create_geopandas_df(df)
        self.fields["selected_food_bank"].choices = [
            (name, name) for name in gdf["name"]
        ]


def generate_map(request):
    G = get_street_network("Manhattan, New York, USA")
    df = load_sample_food_banks()
    gdf = create_geopandas_df(df)

    if request.method == "GET":
        return render(
            request, "dead/location_form.html", {"food_banks": gdf["name"].tolist()}
        )

    elif request.method == "POST":
        user_address = request.POST.get("user_address")
        max_distance = int(request.POST.get("max_distance"))
        selected_food_bank = request.POST.get("selected_food_bank")

        user_coords = geocode_address(user_address) if user_address else None
        dest_coords = (
            gdf.loc[gdf["name"] == selected_food_bank, "coordinates"].values[0]
            if selected_food_bank
            else None
        )

        if user_coords and dest_coords:
            route_details = get_route(G, user_coords, dest_coords)
            map_view = create_map(
                gdf,
                user_location=user_coords,
                max_distance=max_distance,
                route_details=route_details,
            )
            map_html = map_view._repr_html_()
            return JsonResponse({"map_html": map_html, "status": "success"})

        return JsonResponse(
            {"status": "error", "message": "Unable to find location or route"}
        )


def calculate(request):
    food_items = FoodItem.objects.all()
    result = []

    for food_item in food_items:
        monthly_data = (
            FoodItemPurchase.objects.filter(food_item=food_item)
            .values("year_bought", "month_bought")
            .annotate(
                total_bought=Coalesce(Sum("quantity_bought"), 0),
                total_wasted=Coalesce(Sum("amount_wasted"), 0),
                net_consumed=F("total_bought") - F("total_wasted"),
            )
        )

        monthly_consumption = [entry["net_consumed"] for entry in monthly_data]
        optimal_consumption = (
            int(mean(monthly_consumption)) if monthly_consumption else 0
        )

        result.append(
            {
                "name": food_item.name,
                "quantity": optimal_consumption,
                "image_url": food_item.image.url if food_item.image else None,
            }
        )

    return JsonResponse(result, safe=False)


def cart(request):
    return render(request, "dead/cart.html")


def spline(request):
    return render(request, "dead/spline.html")
