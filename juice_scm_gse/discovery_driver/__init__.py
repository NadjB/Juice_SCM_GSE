import json

from lppinstru.discovery import Discovery, c_int
import time, datetime
import zmq


def turn_psu(on_off, channel):
    return json.dumps({
        "CMD": on_off,
        "channel": channel
    })


def turn_on_psu(channel):
    return turn_psu("ON", channel)


def turn_off_psu(channel):
    return turn_psu("OFF", channel)


def process_cmd(cmd_dict, disco):
    cmd = cmd_dict["CMD"]
    if cmd == "ON":
        disco.turn_on()
        return "success"
    else:
        return "unknown command"


class Disco_Driver(Discovery):
    def __init__(self, card=-1):
        super().__init__(card=card)
        self.digital_io_output_enable(0x0001)

    def turn_on(self):
        self.digital_io = 1

    def turn_off(self):
        self.digital_io = 0


def setup_ipc(push_port=9992, pull_port=9991):
    context = zmq.Context()
    push_sock = context.socket(zmq.PUSH)
    push_sock.connect(f"tcp://localhost:{push_port}")
    pull_sock = context.socket(zmq.PULL)
    pull_sock.connect(f"tcp://localhost:{pull_port}")
    return push_sock, pull_sock


def parse_cmd(cmd, disco):
    cmd["result"] = process_cmd(cmd, disco)
    return json.dumps(cmd)


if __name__ == '__main__':
    disco = Disco_Driver()
    push_sock, pull_sock = setup_ipc()
    while True:
        cmd = json.loads(pull_sock.recv_json())
        push_sock.send_json(parse_cmd(cmd, disco))
