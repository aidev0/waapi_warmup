import os
import random
import time
import threading
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
WAAPI_TOKEN = os.getenv("WAAPI_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Lock to coordinate access to shared resources
lock = threading.Lock()


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
    {"instance": "17667", "chatId": "14159648086@c.us"},
    {"instance": "17668", "chatId": "393518024247@c.us"},
    {"instance": "17670", "chatId": "14157250545@c.us"},
    {"instance": "7506", "chatId": "393513919566@c.us"},
    {"instance": "15037", "chatId": "393271696617@c.us"},
    {"instance": "15038", "chatId": "393270196822@c.us"},
    {"instance": "15040", "chatId": "393505357545@c.us"},
    {"instance": "15056", "chatId": "393770833950@c.us"},
    {"instance": "15163", "chatId": "393880932000@c.us"},
    {"instance": "15302", "chatId": "393517696737@c.us"},
    {"instance": "15681", "chatId": "393888078368@c.us"},
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
    now = datetime.now().time()
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
                    message_content = "Generate a random short message, maximum 30 words."
                    messages = [{"role": "user", "content": message_content}]
                    message = get_message(messages)

                    if message:
                        send_message(sender_instance, receiver_instance['chatId'], message)
                    else:
                        print(
                            f"Failed to generate a message from {sender_instance['chatId']} to {receiver_instance['chatId']}")

                else:
                    print(f"{sender_instance['chatId']} has no available receivers this round.")

            # Wait for a random time between 5 to 30 minutes before the next round
            action_wait_time = random.randint(5 * 60, 30 * 60)
            print(f"{sender_instance['chatId']} waiting for {action_wait_time // 60} minutes before the next round.")
            time.sleep(action_wait_time)

        else:
            # Sleep until 06:00 if it's outside allowed messaging hours
            now = datetime.now()
            next_allowed_time = (now + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
            sleep_time = (next_allowed_time - now).total_seconds()
            print(f"{sender_instance['chatId']} sleeping for {int(sleep_time // 3600)} hours until 06:00.")
            time.sleep(sleep_time)


if __name__ == "__main__":
    # Start a separate thread for each instance with a delay between each thread start
    threads = []
    for i, instance in enumerate(instances):
        thread = threading.Thread(target=instance_messaging, args=(instance,))
        threads.append(thread)
        thread.start()

        # Introduce a delay of 5 to 10 minutes before starting the next thread
        if i < len(instances) - 1:
            thread_wait_time = random.randint(5 * 60, 10 * 60)
            print(f"Delaying {thread_wait_time // 60} minutes before starting the next thread.")
            time.sleep(thread_wait_time)

    # Keep the main program running to allow threads to operate
    for thread in threads:
        thread.join()
