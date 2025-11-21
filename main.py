"""
MicroPython Hello World - LED Blink
Blinks the onboard LED to verify the system is working
"""
import machine
import time

# Configure the onboard LED
# For most boards, LED is on pin 25 (Pico) or 'LED' string
try:
    led = machine.Pin('LED', machine.Pin.OUT)
except:
    # Fallback for boards where 'LED' doesn't work
    led = machine.Pin(25, machine.Pin.OUT)

print("Hello World from MicroPython!")
print("Starting LED blink...")

# Blink the LED
while True:
    led.on()
    print("LED ON")
    time.sleep(0.5)
    
    led.off()
    print("LED OFF")
    time.sleep(0.5)
