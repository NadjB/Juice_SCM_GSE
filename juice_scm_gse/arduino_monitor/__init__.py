import serial, time, datetime
import zmq
from glob import glob

def setup_ipc(port=9990):
    context = zmq.Context()
    sock = context.socket(zmq.PUB)
    sock.bind(f"tcp://*:{port}")
    return sock


def setup_serial(socket, port_regex='/dev/ttyACM[0-1]', baudrate=2000000):
    socket.send(f"Status disconnected".encode())
    while True:
        print("try to connect")
        try:
            port = glob(port_regex)
            if len(port):
                com = serial.Serial(port=port[0], baudrate=baudrate)
                if com.is_open:
                    com = serial.Serial(port=port[0], baudrate=baudrate)
                    socket.send(f"Status connected".encode())
                    print("Connected")
                    return com
        except serial.serialutil.SerialException:
            pass
        time.sleep(1.)


def reset_and_flush(ser):
    ser.read_all()
    ser.setDTR(1)
    ser.setDTR(0)
    time.sleep(0.5)
    ser.read_all()


def main():
    socket = setup_ipc()
    ser = setup_serial(socket)
    if ser.is_open:
        with open('/tmp/test_arduino.txt', 'w') as out:
            reset_and_flush(ser)
            out.write(ser.readline().decode())  # comment line
            out.write(ser.readline().decode())  # header columns names
            last_publish = time.time()
            while True:
                try:
                    line = ser.readline().decode()
                    out.write(str(datetime.datetime.now()) + '\t' + line)
                    now = time.time()
                    if (now - last_publish) >= 1.:
                        last_publish = now
                        values = line.split('\t')
                        tempA, tempB, tempC = float(values[-4]), float(values[-3]), float(values[-2])
                        socket.send(f"Temperatures {now},{tempA},{tempB},{tempC}".encode())
                        message = f"Voltages {now}"
                        for v in values[:-4]:
                            message += f",{float(v)}"
                        socket.send(message.encode())

                except serial.serialutil.SerialException:
                    for _ in [None,None]:
                        ser.close()
                        ser = setup_serial(socket)
                        reset_and_flush(ser)
                        ser.readline(),ser.readline()


if __name__ == '__main__':
    main()