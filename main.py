import threading
import time
import os
import uuid
import asyncio
import edge_tts
import pygame
import speech_recognition as sr
import requests
from homeassistant_api import Client
from datetime import datetime
from threading import Timer
from groq import Groq
import yt_dlp
from youtubesearchpython import VideosSearch
import pyjokes
import wikipedia
import subprocess
import webcolors
import pyaudio
import struct
import re
from google import genai
import PIL.Image
import cv2
import sqlite3
import pandas as pd
import numpy as np
from openwakeword.model import Model  # New import for OpenWakeWord

# Initialize pygame mixer (used for TTS and for sound prompts)
pygame.mixer.init()

# Initialize the Gemini client (for cloud completions)
client = genai.Client(api_key="your_api_key")

class Assistant:
    def __init__(self, home_assistant_url, access_token, groqcloud_key, weather_api_key):
        # Home Assistant API client
        self.client = Client(home_assistant_url, access_token)
        self.groqcloud_key = groqcloud_key
        self.weather_api_key = weather_api_key

        # For voice recognition
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

        # TTS: Using edge_tts for streaming TTS with pygame playback.
        self.speak_thread = None

        # Initialize OpenWakeWord model instead of Porcupine.
        self.owwModel = Model(inference_framework='tflite')
        # Set parameters for audio stream
        self.CHUNK_SIZE = 1280
        self.SAMPLE_RATE = 16000

        

    def speak(self, message):
        """Speak the message using edge‑tts streaming and pygame for playback."""
        self.interrupt_speech()
        print("Speaking:", message)
        
        def _speak():
            filename = f"{uuid.uuid4()}.mp3"
            try:
                # Asynchronously stream TTS audio and save to file.
                asyncio.run(self._speak_async(message, filename))
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                # Wait until playback finishes or is interrupted.
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print("Error during TTS playback:", e)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                    
        self.speak_thread = threading.Thread(target=_speak)
        self.speak_thread.start()

    async def _speak_async(self, message, filename):
        communicate = edge_tts.Communicate(message, voice="en-US-AriaNeural")
        with open(filename, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

    def interrupt_speech(self):
        """Stop any ongoing TTS playback."""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print("Error stopping TTS playback:", e)
        if self.speak_thread and self.speak_thread.is_alive():
            self.speak_thread.join(timeout=0.5)

    def getmusic(self, song_term):
        videosSearch = VideosSearch(song_term, limit=2)
        results = videosSearch.result()
        video_id = results["result"][0]["id"]
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'download'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        pygame.mixer.music.load("download.mp3")
        pygame.mixer.music.play()
        mic_temp = sr.Microphone()
        recognizer_temp = sr.Recognizer()
        while pygame.mixer.music.get_busy():
            with mic_temp as source:
                recognizer_temp.adjust_for_ambient_noise(source)
                audio = recognizer_temp.listen(source)
                command = recognizer_temp.recognize_google(audio).lower()
                if "set alarm at" in command:
                    t = self.extract_alarm_time(command)
                    self.set_alarm(t)
                elif "set timer for" in command:
                    duration = self.extract_duration(command)
                    self.set_timer(duration)
                elif "turn on" in command or "turn off" in command:
                    entity_id = self.extract_entity(command)
                    if "turn on" in command:
                        self.turnd_on_device(entity_id)
                    else:
                        self.turn_off_device(entity_id)
                elif "weather" in command:
                    self.get_weather("Ghaziabad")
                elif "time" in command:
                    self.speak(datetime.now().strftime('%I:%M %p'))
                    return datetime.now()
                elif "play" in command:
                    self.getmusic(command.replace("assistant", "").replace("play", "").strip())
                elif "stop" in command:
                    pygame.mixer.music.stop()
                else:
                    self.send_to_groqcloud(command)

    def process_command(self, command):
        print(f"Processing command: {command}")
        if "set alarm at" in command:
            self.setalarm(command)
        elif "set timer for" in command:
            duration = self.extract_duration(command)
            self.set_timer(duration)
        elif "turn on switch " in command:
            entity_id = command.replace("turn on switch", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonswitch(entity_id)
        elif "turn off switch " in command:
            entity_id = command.replace("turn off switch", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnoffswitch(entity_id)
        elif "turn on fan" in command:
            entity_id = command.replace("turn on fan", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonfan(entity_id)
        elif "turn off fan" in command:
            entity_id = command.replace("turn off fan", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnofffan(entity_id)
        elif "turn on light" in command:
            entity_id = command.replace("turn on light", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonlight(entity_id)
        elif "turn off light" in command:
            entity_id = command.replace("turn off light", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnofflight(entity_id)
        elif "set colour of" in command and "to" in command:
            entandcol = command.replace("set colour of", "").replace("to", "").replace("lights", "light")
            parts = entandcol.split()
            ent = parts[0]
            color = parts[1]
            self.setcolor(ent, color)
        elif "set brightness of" in command and "to" in command:
            entandcol = command.replace("set brightness of", "").replace("to", "").replace("lights", "light")
            parts = entandcol.split()
            ent = parts[0]
            brightness = int(parts[1])
            self.lightbrightness(ent, brightness)
        elif "weather" in command:
            self.get_weather("Ghaziabad")
        elif "time" in command:
            t = datetime.now().strftime('%I:%M %p')
            self.speak(t)
        elif "joke" in command:
            j = pyjokes.get_joke()
            self.speak(j)
        elif "wikipedia" in command:
            title = command.replace("ask", "").replace("wikipidia", "").replace("about", "").strip().replace("wikipedia", "")
            summary = wikipedia.summary(title, sentences=4)
            self.speak(summary)
        elif "stop" in command:
            pygame.mixer.music.stop()
        elif "recognise this image" in command:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cv2.imshow("Captured Image", frame)  # Show the image
            cv2.imwrite("selfie.jpg", frame)  # Save the image
            cv2.waitKey(2000)
            self.reco()
            cap.release()
            cv2.destroyAllWindows()
        elif "remember" in command:
            remem = command.replace("remember", "")
            self.remember(remem)
        elif "recall" in command:
            self.whatWasRemembered() 
        elif "clean all memory" in command:
            self.cleanallMemory()  
        elif "forget" in command:
            forget = command.replace("forget", "")
            self.forget(forget)        
        elif "play" in command:
            self.getmusic(command.replace("play", "").strip())
        else:
            self.send_to_groqcloud(command)         

    def get_weather(self, city_name="Ghaziabad"):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={self.weather_api_key}&units=metric"
        response = requests.get(url)
        weather_data = response.json()
        if weather_data["cod"] == 200:
            main_weather = weather_data["main"]
            weather_desc = weather_data["weather"][0]["description"]
            temperature = main_weather["temp"]
            humidity = main_weather["humidity"]
            weather_report = f"The current temperature in {city_name} is {temperature}°C with {weather_desc}. Humidity is {humidity}%."
            self.speak(weather_report)
            print(weather_report)
        else:
            self.speak("Sorry, I couldn't fetch the weather data.")
            print("Error fetching weather data.")

    def send_to_groqcloud(self, command):
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=command,
        )
        print(response.text)
        self.speak(response.text.replace("*", ""))
    
    def remember(self, remem):
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS remember (
                remember TEXT
            )
        """)
        # Insert the value
        cursor.execute("INSERT INTO remember (remember) VALUES (?)", (remem,))
        conn.commit()
        conn.close()
        self.speak("Saved " + remem)  

    def whatWasRemembered(self):
        conn = sqlite3.connect("passwords.db")
        hi = pd.read_sql("SELECT * FROM remember", conn)
        fo = [f"{idx}: {value}" for idx, value in enumerate(hi.iloc[:, 0], start=1)]
        my_string = "\n".join(fo)
        print(my_string)
        if my_string:
            self.speak(my_string)
        else:
            self.speak("No memories found")
            print("No memories found")

    def cleanallMemory(self):
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM remember")
        conn.commit()
        conn.close()
        self.speak("All memories deleted")
        print("All memories deleted")

    def forget(self, forget):
        conn = sqlite3.connect("passwords.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM remember WHERE remember = ?", (forget,))
        conn.commit()
        conn.close()
        self.speak("Deleted")
        print("Deleted")
      
    def turnonlight(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("light")
            ent = "light." + entity_id
            cos.turn_on(entity_id=ent, rgb_color=[0, 0, 0])

    def turnofflight(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("light")
            ent = "light." + entity_id
            cos.turn_off(entity_id=ent)

    def turnonfan(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("fan")
            ent = "fan." + entity_id
            print(ent)
            cos.turn_on(entity_id=ent)

    def turnofffan(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("fan")
            ent = "fan." + entity_id
            print(ent)
            cos.turn_off(entity_id=ent)

    def setcolor(self, entity, color):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("light")
            ent = "light." + entity
            rgbint = webcolors.name_to_rgb(color)
            collist = list(rgbint)
            cos.turn_on(entity_id=ent, rgb_color=collist)

    def lightbrightness(self, entity, brightness):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("light")
            ent = "light." + entity
            lightness = round((brightness / 100) * 255)
            cos.turn_on(entity_id=ent, brightness=lightness)

    def setalarm(self, alarm_time):
        if "for" in alarm_time:
            alarm_time = alarm_time.replace("set alarm for ", "")
        else:
            alarm_time = alarm_time.replace("set alarm at ", "")
        if "p.m." in alarm_time:
            alarm_time = alarm_time.replace("p.m.", "PM")
        else:
            alarm_time = alarm_time.replace("a.m.", "AM")
        timeofal = datetime.strptime(alarm_time, "%I:%M %p").time()
        timeofal = timeofal.replace(hour=timeofal.hour % 12 + (timeofal.hour // 12) * 12)
        timeofal = str(timeofal)
        print(timeofal)
        subprocess.run(f'start powershell python time.py {timeofal}', shell=True)

    def turnonswitch(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("switch")
            ent = "switch." + entity_id
            print(ent)
            cos.turn_on(entity_id=ent)

    def turnoffswitch(self, entity_id):
        with Client('ha ip/apii', 'homeassiatnt_long_lived_acsess_token') as client:
            cos = client.get_domain("switch")
            ent = "switch." + entity_id
            cos.turn_off(entity_id=ent)

    def extract_duration(self, command):
        if "minute" in command:
            return 60
        elif "hour" in command:
            return 3600
        return 0

    def reco(self):
        image = PIL.Image.open('selfie.jpg')
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["What is this image?(if you could recognize a perticular model of lets say smartphone or anything it is better)", image]
        )
        print(response.text)
        self.speak(response.text.replace("*", ""))
        
    def set_timer(self, timer_duration):
        matches = re.findall(r"(\d+)\s*(seconds?|minutes?|hours?)", timer_duration, re.IGNORECASE)
        if not matches:
            print("Invalid time format!")
            return

        total_seconds = 0
        # Convert each found time unit to seconds
        for value, unit in matches:
            value = int(value)
            unit = unit.lower()
            if "hour" in unit:
                total_seconds += value * 3600
            elif "minute" in unit:
                total_seconds += value * 60
            else:
                total_seconds += value  # Seconds directly

        print(f"Timer set for {total_seconds} seconds.")

    def timer_finished(self):
        self.speak("Your timer has finished!")

    def extract_alarm_time(self, command):
        if "time" in command:
            return datetime.now()

    def cleanup(self):
        self.audio_stream.close()
        self.pa.terminate()
        print("Resources cleaned up.")

    def set_alarm(self, alarm_time):
        self.speak(f"Alarm set for {alarm_time}.")

    def listen_to_voice(self):
     CHUNK_SIZE = 1280
     FORMAT = pyaudio.paInt16
     CHANNELS = 1
     RATE = 16000
     COOLDOWN_TIME = 2
     print("Listening for 'hey rhaspy' to activate...")
     audio = pyaudio.PyAudio()
     mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
     last_detection_time = 0 
    # Load OpenWakeWord model
     owwModel = Model(inference_framework='tflite')

     print("Listening for 'Hey Rhasspy'...")

     while True:
        # Get audio
        audio_data = np.frombuffer(mic_stream.read(CHUNK_SIZE), dtype=np.int16)
        
        # Feed to OpenWakeWord model
        prediction = owwModel.predict(audio_data)
        
        # Check if 'Hey Rhasspy' is detected
        if prediction.get("hey_rhasspy", 0) > 0.7:
            current_time = time.time()
            
            # Only trigger if enough time has passed since last detection
            if current_time - last_detection_time > COOLDOWN_TIME:
                print("Hi")
                last_detection_time = current_time
                self.play_sound()  # Play activation sound
                self.listen_for_commands()
                
                # Add a pause after command processing to clear audio buffer
                time.sleep(0.5)
                
                # Flush the audio buffer to prevent false triggers
                while mic_stream.get_read_available() > 0:
                    mic_stream.read(CHUNK_SIZE)
                
                # Update last detection time again to prevent immediate retrigger
                last_detection_time = time.time()
    
                
    def listen_for_commands(self):
     try:
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Listening for command...")
            audio = self.recognizer.listen(source)
        command = self.recognize_command(audio)
        print(f"Detected command: {command}")
        self.process_command(command)
     except sr.UnknownValueError:
        print("Could not understand the audio.")
     except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
     except sr.WaitTimeoutError:
        print("No input detected in time.")
     finally:
        print("Listening for the wake word again...")
        print("done")
                
    def recognize_command(self, audio):
        return self.recognizer.recognize_google(audio).lower()

    def play_sound(self):
        # Play the prompt sound using pygame mixer.
        pygame.mixer.music.load('plop.mp3')  # Ensure 'plop.mp3' is in the same directory.
        pygame.mixer.music.play()

if __name__ == "__main__":
    home_assistant_url = "http://192.168.29.128:8123"
    access_token = "homeassiatnt_long_lived_acsess_token"
    groqcloud_key = ""
    weather_api_key = ""
    
    # Instantiate the assistant with the required credentials.
    assistant = Assistant(home_assistant_url, access_token, groqcloud_key, weather_api_key)
    assistant.listen_to_voice()
