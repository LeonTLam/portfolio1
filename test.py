import threading
import time

def printit():
  start_time = time.time()
  temp_start_time = time.time()
  while True:
    
    if time.time() - temp_start_time >= 5:
        temp_start_time = time.time()
        print ("Hello, World!")
    

printit()

# continue with the rest of your code