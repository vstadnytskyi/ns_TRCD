import visa, serial
rm = visa.ResourceManager('')
rm.list_resources()
serLockIn = serial.Serial('COM2', 9600, 8, 'N', 1, timeout=0.05)
while True:
    command_str = 'Q '+'\r\n'
    serLockIn.write(command_str)
    reply = serLockIn.readline()
    print reply

serLockIn.close()