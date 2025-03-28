import schedule
from pygame import mixer
import time


import sys
mixer.init()

def play_alarm():
        # Play the sound file using pygame mixer
        mixer.music.load('alarm.mp3')  # Make sure 'plop.mp3' is in the same directory or provide full path
        mixer.music.play()
        time.sleep(7)
        return schedule.CancelJob
    

if len(sys.argv) > 1:
    time_value = sys.argv[1]
    print(time_value)
    schedule.every().day.at(time_value).do(play_alarm)
    while True:
     schedule.run_pending()
     time.sleep(1)  # Check every second

    # Stop the loop after the task runs once
     if not schedule.jobs:  
         print("Task completed. Exiting...")
         break
    
else:
    print("No time value received.")



