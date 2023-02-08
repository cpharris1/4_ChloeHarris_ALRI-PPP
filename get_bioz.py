# Short script to capture BIOZ data from Arduino connected via Serial

import serial

ser = serial.Serial(
    # Change port to match system
    #"/dev/serial0", # RPi port
    "COM4", # Windows port
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,  # PARITY_EVEN & ODD have issues
    stopbits=serial.STOPBITS_ONE,
    timeout=1,
)
ser.reset_input_buffer()

def ser_writeread(msg_out):
    # Expects a message to send and returns 1-line response
    ser.write(msg_out.encode("utf-8"))
    print("> " + msg_out)  # Print statement for testing
    while True:
        # waits for response and returns message
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)  # Print statement for testing
            break
    return msg_in

def ser_readBIOZ(filepath):
    # Using readlines(), read until timeout triggers EOF
    # NOTE: This could be buggy, if so swap to hardcoded stop
    # Return the filestamp for later reading
    while True:
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)
            if msg_in == "Measurements start":
                # End of print block, exit loop
                break
    
    fileHandler = open(filepath, "w")
    while True:
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)
            if msg_in == "Measurements done":
                # End of print block, exit loop
                break
            else:
                # Valid data, print to file
                fileHandler.write(msg_in + "\n")
    fileHandler.close()
    return filepath


ser.reset_input_buffer()
ser_writeread("START")

filename = "test-bioz.csv"
folder = "bioz"
filepath = folder + "/" + filename
newBiozFile = ser_readBIOZ(filepath)