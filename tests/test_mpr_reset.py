from functools import cache
import time
import pytest
import subprocess
import serial.tools.list_ports
import mpremote

from mpremote.pyboardextended import Pyboard

# # Static list of devices + port
# DEVICES = [("COM5","rp2"), 
#             ("COM7","stm32"),
#             # ("COM15","esp32"),
#             ("COM17","esp32"),
#             ("COM20","esp8266"),
#             ]
# # dict with mcu - ports
# PORTS = {mcu:port for port, mcu in DEVICES}

DEVICES = {
        'rp2': 'COM5', 
        'stm32': 'COM7', 
        'esp32': 'COM22', 
        'esp8266': 'COM20',
        'esp32s3': 'COM19',}

PORTS_TO_TEST = ["esp32","esp8266","stm32","rp2","esp32s3"]


def all_connected_devices():
    "List attached devices."
    devices = [p.device for p in serial.tools.list_ports.comports()]
    # optionally filter the list of devices
    return sorted(devices)

def reset_mcu(ser_port):
    # initial hard reset

    base = ["mpremote","connect",ser_port] if ser_port else ["mpremote"]
    spr = subprocess.run(base + ["reset"], capture_output=True, universal_newlines=True, timeout=5)
    output = spr.stdout
    if "no device found" in output:
        return "no device found"
    if "failed to access" in output:
        return "failed to access"
    assert spr.returncode == 0
    # allow 2 secs for MCU hard reset to complete
    time.sleep(2)
    return "OK"


@pytest.mark.parametrize("port", PORTS_TO_TEST)
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_eval(reset, port):

    ser_port = DEVICES.get(port)
    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(ser_port)
        if result != "OK":
            pytest.skip(result)


    base = ["mpremote","connect",ser_port, ] if port else ["mpremote",]
    cmd = base + [ "eval", "21+21"]
    spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
    assert spr.returncode == 0
    output = spr.stdout.strip()
    assert output == "42"


@pytest.mark.parametrize("port", PORTS_TO_TEST)
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_no_reset_on_disconnect(reset, port):
    """
    Validate that mpremote does not issue a hard reset when terminating a session
    Requires that the MCU device does not have a 'main.py' file that runs in a loop.
    """
    ser_port = DEVICES.get(port)
    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(ser_port)
        if result != "OK":
            pytest.skip(result)

    # test that resume does not issue a hard reset between connects 
    if ser_port:
        base = ["mpremote","connect",ser_port, "resume"]
    else:
        base = ["mpremote", "resume"]

    cmd = base + ["resume", "exec", "x=1"]
    for n in range(1,4):
        spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
        assert spr.returncode == 0
        output = spr.stdout
        print(f"Port {ser_port}, Test {n} : {output}")
        if ',' in output:
            assert output.split(',')[0].strip() == str(n)
        mpy_cmd = "x = (x+1 if 'x' in dir() else 1);import sys;print(x, ',', sys.platform)"
        cmd = base + ["resume", "exec", mpy_cmd]









