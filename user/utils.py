from twilio.rest import Client
from dotenv import load_dotenv
import logging
import os


load_dotenv()
# set up logging for debuggind
logger = logging.getLogger(__name__)


# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CLIENT = Client(TWILIO_SID, TWILIO_AUTH) if TWILIO_SID and TWILIO_AUTH else None


def send_twilio_notification():
    if not TWILIO_CLIENT:
        logger.error("Twilio credentials not configured.")
        return

    message_text = "Alert! Your item is rotting. Consider making a recipe today!"

    TWILIO_CLIENT.messages.create(
        from_="whatsapp:+14155238886", body=message_text, to="whatsapp:+919685677976"
    )
    image_url = "https://static.toiimg.com/thumb/msid-67569905,width-400,resizemode-4/67569905.jpg"

    TWILIO_CLIENT.messages.create(
        from_="whatsapp:+14155238886",
        media_url=[image_url],
        body="Here's a recipe suggestion! 🍌🥛",
        to="whatsapp:+918657689680",
    )
