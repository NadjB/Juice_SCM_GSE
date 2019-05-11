import serial, time, datetime
import zmq


def setup_ipc(port=9990):
    context = zmq.Context()
    sock = context.socket(zmq.PUB)
    sock.bind(f"tcp://*:{port}")
    return sock


def setup_serial(port='/dev/ttyACM0', baudrate=2000000):
    com = serial.Serial(port=port, baudrate=baudrate)
    return com


def reset_and_flush(ser):
    ser.read_all()
    ser.setDTR(1)
    ser.setDTR(0)
    time.sleep(0.5)
    ser.read_all()


if __name__ == '__main__':
    socket = setup_ipc()
    ser = setup_serial()
    if ser.is_open:
        with open('/tmp/test_arduino.txt','w') as out:
            reset_and_flush(ser)
            out.write(ser.readline().decode()) # comment line
            out.write(ser.readline().decode()) # header columns names
            last_publish = time.time()
            while True:
                line = ser.readline().decode()
                out.write(str(datetime.datetime.now()) + '\t' + line)
                now = time.time()
                if (now - last_publish) >= 1.:
                    last_publish = now
                    values = line.split('\t')
                    tempA,tempB,tempC = float(values[-4]),float(values[-3]),float(values[-2])
                    socket.send(f"Temperatures {now},{tempA},{tempB},{tempC}".encode())