from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886',
    body='🔥 AgentX Test Message Successful!',
    to='whatsapp:+919385567633'
)

print("Message sent:", message.sid)