#!/usr/bin/python

# GPIO port numbers  
import wiringpi2 as wiringpi  
from time import sleep  
wiringpi.wiringPiSetupGpio()  
wiringpi.pinMode(24, 1)      # sets GPIO 24 to output  
wiringpi.digitalWrite(24, 0) # sets port 24 to 0 (0V, off)  
sleep(10)  
wiringpi.digitalWrite(24, 1) # sets port 24 to 1 (3V3, on)  
sleep(10)  
wiringpi.digitalWrite(24, 0) # sets port 24 to 0 (0V, off)  
wiringpi.pinMode(24, 0)      # sets GPIO 24 back to input Mode  

