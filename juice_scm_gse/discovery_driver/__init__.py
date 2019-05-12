import json

from lppinstru.discovery import Discovery, c_int
import time, datetime
import zmq
import functools

commands = {}


class DiscoCommand:
    def __init__(self,func):
        functools.update_wrapper(self, func)
        self.func = func
        commands[func.__name__] = func

    def make_cmd(self, channel, **kwargs):
        payload =  {
            "CMD": self.func.__name__,
            "channel": channel
        }
        payload.update(kwargs)
        return json.dumps(payload)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Disco_Driver(Discovery):
    def __init__(self, card=-1):
        super().__init__(card=card)
        self.digital_io_output_enable(0x0001)

    def turn_on(self):
        self.digital_io = 1

    def turn_off(self):
        self.digital_io = 0


@DiscoCommand
def do_psd(channel, snapshots_count=10):

    time.sleep(3.)


@DiscoCommand
def do_dynamic_tf(channel):
    time.sleep(3.)


@DiscoCommand
def do_static_tf(channel):
    time.sleep(3.)


@DiscoCommand
def turn_on_psu(disco:Disco_Driver):
    disco.turn_on()


@DiscoCommand
def turn_off_psu(disco:Disco_Driver):
    disco.turn_off()


@DiscoCommand
def do_measurements(disco):
    for measurement in [do_psd, do_dynamic_tf, do_static_tf]:
        turn_on_psu(disco)
        measurement(disco)
        turn_off_psu(disco)
        time.sleep(5.)


def process_cmd(cmd_dict, discos):
    cmd = cmd_dict["CMD"]
    try:
        commands[cmd](discos[cmd_dict["channel"]])
        return "success"
    except:
        return "unknown command"


def setup_ipc(push_port=9992, pull_port=9991):
    context = zmq.Context()
    push_sock = context.socket(zmq.PUSH)
    push_sock.connect(f"tcp://localhost:{push_port}")
    pull_sock = context.socket(zmq.PULL)
    pull_sock.connect(f"tcp://localhost:{pull_port}")
    return push_sock, pull_sock


def parse_cmd(cmd, discos):
    cmd["result"] = process_cmd(cmd, discos)
    return json.dumps(cmd)


def main():
    disco = Disco_Driver()
    discos = {
        "CHX": disco, "CHY": disco, "CHZ": disco
    }
    push_sock, pull_sock = setup_ipc()
    while True:
        cmd = json.loads(pull_sock.recv_json())
        push_sock.send_json(parse_cmd(cmd, discos))

if __name__ == '__main__':
    main()
