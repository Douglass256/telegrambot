import telepot
import os
import random
import string
import time
import requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_API')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
RENDER_URL = os.getenv('RENDER_EXTERNAL_URL')

if not all([TOKEN, HUGGINGFACE_API_KEY, RENDER_URL]):
    raise ValueError("Missing one or more environment variables!")

SECRET = ''.join(random.choice(string.ascii_letters) for _ in range(20))
bot = telepot.Bot(token=TOKEN)

# --------------------- AI RESPONSE ---------------------
def ai_response(prompt: str):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    model = "HuggingFaceH4/zephyr-7b-beta"


    data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200, "temperature": 0.7}
    }

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers=headers,
            json=data,
            timeout=40
        )
        response.raise_for_status()
        output = response.json()

        if isinstance(output, list) and len(output) > 0:
            return output[0].get("generated_text", "").strip()
        elif isinstance(output, dict) and "generated_text" in output:
            return output["generated_text"].strip()
        else:
            return "I couldn’t generate a response right now. Try again later."

    except Exception as e:
        print(f"AI Error: {e}")
        return "Sorry, I had trouble connecting to AI service."

# --------------------- SAFE MESSAGE SENDER ---------------------
def safe_send_message(chat_id, text):
    try:
        bot.sendMessage(chat_id, text)
    except telepot.exception.TooManyRequestsError as e:
        wait = e.args[2]["parameters"]["retry_after"]
        time.sleep(wait + 1)
        bot.sendMessage(chat_id, text)

# --------------------- FLASK APP ---------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Fitness Coach Bot is running!", 200

@app.route(f'/{SECRET}', methods=['POST'])
def webhook():
    update = request.get_json()
    print(update)

    if not update:
        return "no update", 400

    message = update.get("message") or update.get("channel_post")
    if not message:
        return "no message", 400

    chat_id = message["chat"]["id"]
    chat_type = message["chat"].get("type")
    text = message.get("text", "")

    if chat_type in ["channel", "supergroup", "group"]:
        if "motivation" in text.lower():
            safe_send_message(chat_id, "Stay strong, every effort counts 💪")
        else:
            safe_send_message(chat_id, "Hello team! I’m here to help with your fitness journey.")
    elif chat_type == "private":
        if text.startswith("/start"):
            safe_send_message(chat_id, "Hello! I’m your AI fitness coach. How can I help you today?")
        elif text.startswith("/help"):
            safe_send_message(chat_id, "You can ask about fitness, nutrition, or motivation. Try typing 'give me a workout tip'.")
        elif text.startswith("/motivation"):
            safe_send_message(chat_id, "Pain is temporary. Progress is permanent. Keep going! 💥")
        else:
            reply = ai_response(text)
            safe_send_message(chat_id, reply)

    return "OK", 200

# --------------------- SET WEBHOOK ON STARTUP ---------------------
with app.app_context():
    webhook_url = f"{RENDER_URL}/{SECRET}"
    bot.setWebhook(webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

