import os
import random
import time
import threading
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pytz import timezone
import pytz

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
WAAPI_TOKEN = os.getenv("WAAPI_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROMPT = """
You are a random whatsapp message generator in italian language. 
Generate a message between 10 and 25 words, with common, random responses 
between two people that can look credible. 
Just one message. Don't put the massage into quotes. 
Don't write nothing before or after the message. 
Never use spam words that whatsapp may flag as spam. 
Choose a random topic for the message. 
Don't talk about the same topic in every message.
Don't talk abut film or movies.
Choose a number between 1 to 34 and then talk about the topic related to that number.
1) food
2) theatre
3) activities in Rome
4) other cities of Italy
5) ask about life
6) personal questions 
7) Italian culture
8) Italian music
9) Italian cities 
10 Italian history or Italian art
11) Italian literature 
12) Italian fashion 
13) Italian design
14) Italian architecture
15) Italian sports
16) Italian traditions
17) Italian holidays
19) Italian lifestyle
20) Italian language
21) Italian people
22) Italian celebrities 
23) Italian politics
24) Italian economy
25) Italian geography 
26) Italian education 
27) Italian science
28) technology
29) Italian religion 
30) modern AI
31) tech 
32) sales 
33) b2b 
34) b2c.

Ends every message saying that you are a guy named Giampiero."""

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Lock to coordinate access to shared resources
lock = threading.Lock()

# Set your desired timezone (PST)
pst_tz = timezone('America/Los_Angeles')


# Function to generate a random message using a specific model with retries
def get_message(messages, model="gpt-4o-mini", retries=5):
    trial = 0
    while trial < retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            message = response.choices[0].message.content
            if len(message.split()) <= 30:  # Ensure the message is within 30 words
                return message
            else:
                raise ValueError("Generated message exceeds the expected length.")
        except Exception as e:
            print(f"Error generating message: {e}")
            time.sleep(1)
            trial += 1
    return None


# List of instances with their chat IDs
instances = [
    {"instance": "7506", "chatId": "393513919566@c.us"},
    {"instance": "15037", "chatId": "393271696617@c.us"},
    {"instance": "15038", "chatId": "393270196822@c.us"},
    {"instance": "15040", "chatId": "393505357545@c.us"},
    {"instance": "15056", "chatId": "393770833950@c.us"},
    {"instance": "15163", "chatId": "393880932000@c.us"},
    {"instance": "15302", "chatId": "393517696737@c.us"},
    {"instance": "15681", "chatId": "393888078368@c.us"},
    {"instance": "17668", "chatId": "393518024247@c.us"},
    {"instance": "17670", "chatId": "14157250545@c.us"},
    {"instance": "18013", "chatId": "393513272910@c.us"},
    {"instance": "18023", "chatId": "393770833950@c.us"},
    {"instance": "18285", "chatId": "393701351084@c.us"},
    {"instance": "18363", "chatId": "393514372998@c.us"}
]


# Function to send a message using the Waapi API
def send_message(sender_instance, receiver_chat_id, message):
    url = f"https://waapi.app/api/v1/instances/{sender_instance['instance']}/client/action/send-message"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {WAAPI_TOKEN}"
    }
    payload = {
        "chatId": receiver_chat_id,
        "message": message
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Sent message from {sender_instance['chatId']} to {receiver_chat_id}")


# Function to check if the current time is within the allowed messaging hours
def is_allowed_time():
    now = datetime.now(pytz.utc).astimezone(pst_tz).time()  # Convert UTC to PST
    return not (now >= datetime.strptime("23:00", "%H:%M").time() or now <= datetime.strptime("06:00", "%H:%M").time())


# Function for each instance thread to run its messaging logic
def instance_messaging(sender_instance):
    while True:
        if is_allowed_time():
            with lock:
                # Randomly select a receiver instance that is not the sender
                available_receivers = [inst for inst in instances if inst["chatId"] != sender_instance["chatId"]]

                if available_receivers:
                    receiver_instance = random.choice(available_receivers)

                    # Generate a random message using the get_message function
                    message_content = PROMPT
                    messages = [{"role": "user", "content": message_content}]
                    message = get_message(messages)

                    if message:
                        send_message(sender_instance, receiver_instance['chatId'], message)
                    else:
                        print(
                            f"Failed to generate a message from {sender_instance['chatId']} to {receiver_instance['chatId']}")

                else:
                    print(f"{sender_instance['chatId']} has no available receivers this round.")

            # Wait for a random time between 5 and 30 minutes before the next round
            action_wait_time = random.randint(300, 1800)  # 300 seconds (5 minutes) to 1800 seconds (30 minutes)
            print(f"{sender_instance['chatId']} waiting for {action_wait_time // 60} minutes before the next round.")
            time.sleep(action_wait_time)

        else:
            # Every 10 minutes, print that the instance is alive but sleeping
            while not is_allowed_time():
                print(f"{sender_instance['chatId']} WhatsApp warmer is sleeping now but instance is alive. "
                      f"Getting back to work at 6 AM PST.")
                time.sleep(600)  # Sleep for 10 minutes


if __name__ == "__main__":
    # Start a separate thread for each instance with a delay between each thread start
    threads = []
    for i, instance in enumerate(instances):
        thread = threading.Thread(target=instance_messaging, args=(instance,))
        threads.append(thread)
        thread.start()

        # Introduce a delay of 1 to 5 minutes before starting the next thread
        thread_wait_time = random.randint(60, 180)  # 120 seconds (2 minutes) to 600 seconds (10 minutes)
        print(f"Delaying {thread_wait_time // 60} minutes before starting the next thread.")
        time.sleep(thread_wait_time)

    # Keep the main program running to allow threads to operate
    for thread in threads:
        thread.join()
