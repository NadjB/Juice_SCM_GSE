import serial, time, datetime
import zmq
from glob import glob
import juice_scm_gse.config as cfg
from  juice_scm_gse.utils import mkdir
from re import search


def setup_ipc(port=9990, portPair=9991):
    context = zmq.Context()
    sock = context.socket(zmq.PUB)
    sock.bind(f"tcp://*:{port}")

    sockPair = context.socket(zmq.PAIR)
    sockPair.bind(f"tcp://*:{portPair}")
    return sock, sockPair



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
    socket, sockPair = setup_ipc()
    ser = setup_serial(socket)
    nbrIteration = 0
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
                    msg = sockPair.recv(flags=zmq.NOBLOCK)
                    msg = msg.decode("utf-8")
                    if "alim" in msg:
                        ser.write(f"{msg}".encode())

                    if "ASIC_JUICEMagic3" in msg:
                        out.write('\t' + msg)

                except zmq.ZMQError:
                    pass

                try:
                    line = ser.readline().decode()                                                                      #get and decode the data on the serial communication
                    out.write(str(datetime.datetime.now()) + '\t' + line)
                    now = time.time()

                    values = line.split('\t')

                    for val in values:
                        if "_CH" in val:
                            nbrIteration = 0

                    if nbrIteration == 0:                                                                               #la premiere iteration n'a que les entête
                        pass
                    elif nbrIteration == 1:
                        valuesVoltage = values[:-1]
                    else:
                        valuesVoltage = [float(vOld) + float(vNew) for vOld, vNew in zip(valuesVoltage, values[:-1])]

                    nbrIteration += 1

                    if (now - last_publish) >= 0.33:                                                                    #Wait 0.3 second just because (old:temp measurments are slow)
                        last_publish = now

                        #values = line.split('\t')
                        #tempA, tempB, tempC = float(values[-4]), float(values[-3]), float(values[-2])
                        #tempA, tempB, tempC = float(10), float(11), float(12)
                        #socket.send(f"Temperatures {now},{tempA},{tempB},{tempC}".encode())

                        message = f"Voltages {now}"

                        for v in valuesVoltage:                                                                         #values[:-1] exept the last one
                            v = float(v)
                            if nbrIteration > 1:
                                v = v / (nbrIteration-1)
                            message += f",{v}"

                        nbrIteration = 0

                        socket.send(message.encode())
                        out.flush()


                except serial.serialutil.SerialException:
                    for _ in [None,None]:
                        ser.close()
                        ser = setup_serial(socket)
                        reset_and_flush(ser)
                        ser.readline(),ser.readline()

