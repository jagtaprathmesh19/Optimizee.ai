import os
import logging
import cv2
from PIL import Image
from dotenv import load_dotenv

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FoodItem, DetectedObject
from .serializers import FoodItemSerializer, DetectedObjectSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication


from ultralytics import YOLO

import google.generativeai as genai


load_dotenv()

# set up logging for debuggind
logger = logging.getLogger("myapp")

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# YOLO Model for Object Detection
YOLO_MODEL = YOLO("yolov8n.pt")
YOLO_MODEL.to("cpu")


def extract_expiry_date_from_image(image):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            [
                "Extract the expiry date from this image. Only return the date, e.g., '12th Jan 2024'",
                Image.open(image),
            ]
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None


def index(request):
    return render(request, "base.html")


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def upload_image_and_voice(request):
    if request.method == "POST":
        food_name = request.POST.get("food_name", "")
        expiry_date = request.POST.get("expiry_date", "")
        uploaded_image = request.FILES.get("image")

        if uploaded_image:
            fs = FileSystemStorage()
            filename = fs.save(uploaded_image.name, uploaded_image)
            image_url = fs.url(filename)
            expiry_date = extract_expiry_date_from_image(uploaded_image) or expiry_date

        if food_name and expiry_date:
            FoodItem.objects.create(
                user=request.user,
                name=food_name,
                expiration_date=expiry_date,
                image=uploaded_image,
            )
            return JsonResponse(
                {"expiry_date": expiry_date, "redirect_url": "/user/dashboard"}
            )

    return render(request, "user/voice_input_form.html")


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard(request):
    food_items = ...
    try:
        food_items = FoodItem.objects.get(user=request.user.id)
        for item in food_items:
            item.update_status()

        return render(request, "/user/dashboard.html", {"food_items": food_items})
    except FoodItem.DoesNotExist:
        logger.error(f"The user not found : {request.user.username}")
        raise Warning("User not Found!")


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    try:
        food_items = FoodItem.objects.get(user=request.user.id)
        serializer = FoodItemSerializer(food_items, many=True)
        return Response({"food_items": serializer.data})
    except FoodItem.DoesNotExist:
        logger.error(f"The user not found : {request.user.username}")
        raise Warning("User not Found!")


@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def video_feed(request):
    def gen_frames():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = YOLO_MODEL(frame)
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = result.names[int(box.cls[0].item())]
                    confidence = round(box.conf[0].item(), 2)
                    DetectedObject.objects.create(
                        name=label, confidence=confidence, user=request.user
                    )
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            _, jpeg = cv2.imencode(".jpg", frame)
            frame = jpeg.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")
        cap.release()

    return StreamingHttpResponse(
        gen_frames(), content_type="multipart/x-mixed-replace; boundary=frame"
    )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def detected_objects(request):
    objects = DetectedObject.objects.filter(user=request.user)
    serializer = DetectedObjectSerializer(objects, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def detect(request):
    return render(request, "user/fruit_detection.html")


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def community(request):
    return render(request, "user/community.html")


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def recipe_slider(request):
    return render(request, "user/recipee_slider.html")


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def rotting_index(request):
    return render(request, "user/rotting.html")
