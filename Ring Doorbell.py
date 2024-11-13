# All imports necessary for this project
import discord
import asyncio
import datetime
import subprocess
import threading
import time

from gpiozero import Button, DistanceSensor
from picamera import PiCamera

###############################################################

# Replace with your bot's token and the channel ID where you want to send the message
TOKEN = 555 # Replace with bot token
CHANNEL_ID = 555  # Replace with your Discord channel ID

# set up distance sensor and camera and button
BUTTON_PIN = 23
button = Button(BUTTON_PIN)
sensor = DistanceSensor(echo=18, trigger=17) # These can all be adjusted for your pin set up
camera = PiCamera()
camera.resolution = (640,480)

# Path to the sound file you want to play
SOUND_FILE = "Door Bell Sound Effect.mp3"

# Create an instance of the Discord bot
client = discord.Client(intents=discord.Intents.default())

# Flag to track the motion detection pause state
motion_paused = False
pause_timer = None

###############################################################

# Communicates the appropriate message and image to the Discord RingBot
# RingBot sends those notifications to the channel
async def capture_and_send_photo(message, isButton):
    # if the doorbell was rang, play a sound
    if(isButton): 
        print("Playing sound...")
        subprocess.run(['cvlc', '--play-and-exit', SOUND_FILE])
        
    filename = f"/home/adamdanrdp/Pictures/image_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    print("Capturing photo...")
    camera.capture(filename)
    
    # Send the image to Discord
    print("Sending to Discord...")
    channel = client.get_channel(CHANNEL_ID)
    if channel is not None:
        with open(filename, 'rb') as image_file:
            await channel.send(f'{message}! Here is a Photo: ', file=discord.File(image_file))
        print("Image sent!")
    else:
        print("Channel not found.")

# Event handler for when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    button.when_pressed = button_pressed
    
    motion_thread = threading.Thread(target=detect_motion, daemon=True)
    motion_thread.start()

###############################################################

# The event handlers run the capture_and_send_photo method with the appropriate parameter
# Button press handler
def button_pressed():
    print("Button pressed")
    asyncio.run_coroutine_threadsafe(capture_and_send_photo("Someone Rang Your Doorbell", True), client.loop) # Since this event handler is for the button (doorbell) the isButton parameter is true

# Motion Detected handler
def detect_motion():
    global motion_paused
    print("Waiting for motion...")
    
    while True:
        if motion_paused:
            # If motion is paused, wait a little before checking again
            time.sleep(1)
            continue
        
        initDist = get_distance()
        time.sleep(0.25) # Adjust time between calculations
        currDist = get_distance()

        dist_change = abs(initDist - currDist)
        
        # Checks if there is 5 inches of movement within fraction of second
        if(dist_change > 5): # Adjust threshhold of movement in inches
            print("Motion detected!")
            asyncio.run_coroutine_threadsafe(capture_and_send_photo("There is Motion at Your Door", False), client.loop)

             # Pause motion detection for 60 seconds
            motion_paused = True
            print("Pausing motion detection for 60 seconds...")
            
            # Use a timer to resume motion detection after 60 seconds
            global pause_timer
            pause_timer = threading.Timer(60, pause_motion_detection)
            pause_timer.start()

# Function to handle pausing the motion detection
def pause_motion_detection():
    global motion_paused
    motion_paused = False
    print("Motion detection resumed.")

# checks how far an object is from the sensor
def get_distance():
    print("Measuring Distance")
    inches = (sensor.distance * 100) / 2.5
    print(f'Distance is {inches} inches')
    return inches

###############################################################
client.run(TOKEN) # Run the instance of our discord bot