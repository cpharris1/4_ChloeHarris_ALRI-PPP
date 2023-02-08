import time
import serial

print("Waiting for user input and sending messages over serial")

# Read serial port from transmitting Arduino
ser = serial.Serial("/dev/serial0",
                    baudrate=250000,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1)
ser.reset_input_buffer()

while True:
    message_out = input()
    ser.write( message_out.encode('utf-8') )
    print('>' + message_out)