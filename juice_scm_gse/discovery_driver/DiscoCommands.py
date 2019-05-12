import json


def turn_psu(on_off, channel):
    return json.dumps({
        "CMD": on_off,
        "channel": channel
    })


def turn_on_psu(channel):
    return turn_psu("ON", channel)


def turn_off_psu(channel):
    return turn_psu("OFF", channel)


def process_cmd(cmd_dict,disco):
    cmd = cmd_dict["CMD"]
    if CMD == "ON":
        disco.turn_on()
        return "success"
    else:
        return "unknown command"
