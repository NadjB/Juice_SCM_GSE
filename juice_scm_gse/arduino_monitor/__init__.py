import serial, time, datetime
import zmq
from glob import glob
import juice_scm_gse.config as cfg
from  juice_scm_gse.utils import mkdir


def setup_ipc(port=9990):
    context = zmq.Context()
    sock = context.socket(zmq.PUB)
    sock.bind(f"tcp://*:{port}")
    return sock


def setup_serial(socket, port_regex='/dev/ttyACM[0-1]', baudrate=2000000):                                              #Get the Arduino data via the serial communication
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
        path = cfg.global_workdir.get()+"/monitor"
        mkdir(path)                                                                                                     #create a "monitor" file in the working directory
        fname = f"{path}/all-{str(datetime.datetime.now())}.txt"                                                        #create a file with the current date to dump the data
        print(fname)
        with open(fname, 'w') as out:
            reset_and_flush(ser)
            out.write(ser.readline().decode())  # comment line
            out.write(ser.readline().decode())  # header columns names
            last_publish = time.time()
            while True:
                try:
                    line = ser.readline().decode()                                                                      #get and decode the data on the serial communication
                    out.write(str(datetime.datetime.now()) + '\t' + line)
                    now = time.time()
                    if (now - last_publish) >= 1.:                                                                      #Whait 1 second because temp measurments are slow
                        last_publish = now
                        values = line.split('\t')
                        #tempA, tempB, tempC = float(values[-4]), float(values[-3]), float(values[-2])
                        #tempA, tempB, tempC = float(10), float(11), float(12)
                        #socket.send(f"Temperatures {now},{tempA},{tempB},{tempC}".encode())

                        message = f"Voltages {now}"
                        for v in values[:-1]:                                                                           #values[:-1] exept the last one
                            message += f",{float(v)}"

                        #print(values[0])
                        #print(message)
                        socket.send(message.encode())

                except serial.serialutil.SerialException:
                    for _ in [None,None]:
                        ser.close()
                        ser = setup_serial(socket)
                        reset_and_flush(ser)
                        ser.readline(),ser.readline()


