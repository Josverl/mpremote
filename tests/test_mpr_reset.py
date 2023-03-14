from functools import cache
import time
import pytest
import subprocess
import serial.tools.list_ports


# Static list of devices + port
DEVICES = [("COM5","rp2"), 
            ("COM7","stm32"),
            ("COM15","esp32"),
            ("COM17","esp32"),
            ("COM20","esp8266"),
            ]


def all_connected_devices():
    "List attached devices."
    devices = [p.device for p in serial.tools.list_ports.comports()]
    # optionally filter the list of devices
    return sorted(devices)

def reset_mcu(port):
    # initial hard reset

    base = ["mpremote","connect",port] if port else ["mpremote"]
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


@pytest.mark.parametrize("port", all_connected_devices())
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_eval(reset, port):

    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(port)
        if result != "OK":
            pytest.skip(result)


    base = ["mpremote","connect",port, ] if port else ["mpremote",]
    cmd = base + [ "eval", "21+21"]
    spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
    assert spr.returncode == 0
    output = spr.stdout.strip()
    assert output == "42"


@pytest.mark.parametrize("port", all_connected_devices())
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_no_reset_on_disconnect(reset, port):
    """
    Validate that mpremote does not issue a hard reset when terminating a session
    Requires that the MCU device does not have a 'main.py' file that runs in a loop.
    """
    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(port)
        if result != "OK":
            pytest.skip(result)

    # test that resume does not issue a hard reset between connects 
    mpy_cmd = "x = (x+1 if 'x' in dir() else 1);import sys;print(x, ',', sys.platform)"
    if port:
        base = ["mpremote","connect",port, "resume"]
    else:
        base = ["mpremote", "resume"]
    cmd = base + ["resume", "exec", mpy_cmd]
    for n in range(1,4):
        spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
        assert spr.returncode == 0
        output = spr.stdout
        print(f"Port {port}, Test {n} : {output}")
        if ',' in output:
            assert output.split(',')[0].strip() == str(n)


@pytest.mark.parametrize("port", all_connected_devices())
def test_mpremote_no_bootloader(port):

    cmd_check =["exec", "import machine;print('OK' if 'reset' in dir(machine) else 'skip')"]
    if port:
        base = ["mpremote","connect",port, "resume"]
    else:
        base = ["mpremote", "resume"]
    # initial hard reset
    result = reset_mcu(port)
    if result != "OK":
        pytest.skip(result)


    output = subprocess.run(base + cmd_check, capture_output=True, universal_newlines=True)
    assert output.returncode == 0
    if output.stdout.strip() == "skip":
        pytest.skip("no machine.reset() function")
    output = subprocess.run(base + ["exec", "import machine, time;time.sleep_ms(100);machine.reset()"], capture_output=True, universal_newlines=True, timeout=5)
    assert output.returncode == 0
    # allow 2 secs for MCU hard reset to complete
    time.sleep(2)
    output = subprocess.run(base + ["exec", "print('restart OK')"], capture_output=True, universal_newlines=True, timeout=5)
    assert output.returncode == 0
    assert output.stdout.strip() == "restart OK"



    







