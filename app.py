import telepot
import re
import os
import random
import random
import string
import time
import requests
from dotenv import load_dotenv, dotenv_values
from flask import Flask, render_template, session, url_for, redirect, request
from telepot.namedtuple import *

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_API')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

if not all([TOKEN, HUGGINGFACE_API_KEY]):
    raise ValueError("Missing one or more enviroment variables!")

SECRET = ''.join(random.choice(string.ascii_letters) for i in range(20))


#telepot.api.set_proxy('http://proxy.server:3128')
bot = telepot.Bot(token=TOKEN)


# HuggingFace text generation function
def ai_response(prompt: str):
    """Get AI-generated response from HuggingFace model."""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
    }
    
    model = "mistralai/Mitral-7B-Instruct-v0.2"
    
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
        
        #extract generated text safely
        if isinstance(output, list) and len(output) > 0:
            return output[0].get("generated_text", "").strip()
        elif isinstance(output, dict) and "generated_text" in output:
            return output["generated_text"].strip()
        else:
            return " I could not generate a response right now. Try again later"
        
    except Exception as e:
        print(f"AI Error: {e}")
        return " Sorry, I had trouble connecting to AI service."


#def processing(msg):
    if 'chat' in msg and msg['chat']['type'] == 'channel':
        return
    
    id = msg['from']['id']
    
    if 'text' in msg:
        msg['text'] = str(msg['text'])
        msg['type'] = 'text'
        
    elif 'data' in msg:
        msg['type'] = 'callback'
        msg['text'] = f"%callback {msg['data']}"
        
    else:
        msg['type'] = 'nonetext'
        types = ['audio', 'voice', 'document', 'photo', 'sticker', 'video', 'contact', 'location']
        
        for type in types:
            if type in msg:
                msg['text'] = f"%{type}"
                break

    if 'text' in msg:
        for entry in regrex:
            if re.match(entry, msg['text']):
                matches = re.match(entry, msg['text']).groups()
                parser(msg, list(matches))
                return
            
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, this is your fitness coach, how can I assist you today?", 200


@app.route(f'/{SECRET}', methods=['POST'])
def webhook():
    update = request.get_json()
    print(update)
    
    if not update:
        return "no update", 400
    
    message = update.get("message") or update.get("channel_post")
    if not message:
        return "No message", 400
    
    chat = message['chat']
    chat_id = chat['id']
    chat_type = chat.get("type")
    text = message.get("text", "")
    
    # Channel / Group message handling
    if chat_type in ["channel", "supergroup", "group"]:
        if "motivation" in text.lower():
            bot.sendMessage(chat_id, "Stay strong, every effort counts.")
        else:
            bot.sendMessage(chat_id, "Hello mwe bayaye, I am here to help with your fitness and coaching journeys!")
            return "OK", 200
        
        # Handling Private messages
    elif chat_type == "private":
        if text.startswith("/start"):
            bot.sendMessage(chat_id, "Hello, I am your personal fitness coach powered by AI. How canI help you today?")
        elif text.startswith("/help"):
            bot.sendMessage(chat_id, "You can ask me anything related to fitness, nutrition, and wellness. Just type your question!")
        elif text.startswith("/motivation"):
            bot.sendMessage(chat_id, "Pain is temporary, if it is the obstacle to the way. Then it becomes the way. But if it is not, then just let it pass!")
        else:
            
            # Use AI response
            reply = ai_response(text)
            bot.sendMessage(chat_id, reply)
        return "OK", 200
    
    return "OK", 200

 

# Set webhook Automatically
@app.before_first_request
def set_webhook():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    webhook_url = f"{render_url}/{SECRET}"
    bot.setWebhook(webhook_url)
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
            

        

