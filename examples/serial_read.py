import time
import serial

print("Reading serial port for incoming messages from Arduino")

# Start script
ser = serial.Serial("/dev/serial0",
                    baudrate=250000,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout= 1)  
    

ser.reset_input_buffer()

while True:
    if ser.in_waiting > 0:      
        message_in = ser.readline().decode('utf-8',errors='replace').strip()
        print( message_in )
#         print(ser.read())

