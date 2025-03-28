import schedule
from pygame import mixer
import time
import sys
import asyncio
import edge_tts

# Initialize the mixer for playing sounds
mixer.init()

async def speak_message(message):
    """Uses Edge TTS to speak the reminder message twice."""
    communicate = edge_tts.Communicate(message, voice="en-US-AriaNeural")
    await communicate.save("reminder.mp3")  # Save the speech to a file

    # Play the generated speech file
    mixer.music.load("reminder.mp3")
    mixer.music.play()
    time.sleep(5)  # Wait for the speech to finish

    # Speak the message a second time
    mixer.music.load("reminder.mp3")
    mixer.music.play()
    time.sleep(5)

def play_alarm(message):
    """Plays an alarm sound and calls Edge TTS to read the message."""
    print(f"🔔 Reminder: {message}")

    # Play alarm sound
    mixer.music.load("alarm.mp3")  # Ensure the file exists
    mixer.music.play()

    # Wait for a short duration before speaking
    time.sleep(2)

    # Use asyncio to run Edge TTS
    asyncio.run(speak_message(message))

    return schedule.CancelJob  # Remove the job after execution

# Check if time and message arguments are provided
if len(sys.argv) > 2:
    time_value = sys.argv[1]
    reminder_message = " ".join(sys.argv[2:])  # Combine message words
    print(f"Setting reminder at {time_value}: {reminder_message}")

    # Schedule the reminder
    schedule.every().day.at(time_value).do(play_alarm, reminder_message)

    while True:
        schedule.run_pending()
        time.sleep(1)  # Check every second

        # Exit when all jobs are done
        if not schedule.jobs:
            print("All reminders completed. Exiting...")
            break

else:
    print("Usage: python script.py <HH:MM> <Reminder message>")
