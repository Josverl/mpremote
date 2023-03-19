from functools import cache
import time
from typing import List, Tuple
import pytest
import subprocess
import serial.tools.list_ports
import keyboard

from mpremote.pyboardextended import Pyboard

# mark all tests
pytestmark = [pytest.mark.mpremote, pytest.mark.serial]


@cache
def all_connected_devices():
    "List serial ports with attached devices and mcu_port."
    devices = [p.device for p in serial.tools.list_ports.comports()]

    d2: List[Tuple[str, str]] = []
    for ser_port in devices:
        cmd = ["mpremote", "connect", ser_port, "exec", "import sys;print(sys.platform)"]
        spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
        mcu_port = spr.stdout.strip()
        if "no device found" in mcu_port:
            continue
        if "failed to access" in mcu_port:
            continue
        d2.append((mcu_port, ser_port))
    # optionally filter the list of devices
    return sorted(d2)


def reset_mcu(ser_port):
    # initial hard reset

    base = ["mpremote", "connect", ser_port] if ser_port else ["mpremote"]
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


@pytest.mark.parametrize("mcu_port, ser_port", all_connected_devices())
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_eval(reset, mcu_port, ser_port):
    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(ser_port)
        if result != "OK":
            pytest.skip(result)

    base = (
        [
            "mpremote",
            "connect",
            ser_port,
        ]
        if ser_port
        else [
            "mpremote",
        ]
    )
    cmd = base + ["eval", "21+21"]
    spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
    assert spr.returncode == 0
    output = spr.stdout.strip()
    assert output == "42"


@pytest.mark.parametrize("mcu_port, ser_port", all_connected_devices())
@pytest.mark.parametrize("reset", ["no_reset", "hard_reset"])
def test_mpremote_no_reset_on_disconnect(reset,mcu_port, ser_port):
    """
    Validate that mpremote does not issue a hard reset when terminating a session
    Requires that the MCU device does not have a 'main.py' file that runs in a loop.
    """
    if reset == "hard_reset":
        # initial hard reset
        result = reset_mcu(ser_port)
        if result != "OK":
            pytest.skip(result)

    # test that resume does not issue a hard reset between connects
    if ser_port:
        base = ["mpremote", "connect", ser_port, "resume"]
    else:
        base = ["mpremote", "resume"]

    cmd = base + ["resume", "exec", "x=1"]
    for n in range(1, 4):
        spr = subprocess.run(cmd, capture_output=True, universal_newlines=True, timeout=5)
        assert spr.returncode == 0
        output = spr.stdout
        print(f"Port {ser_port}, Test {n} : {output}")
        if "," in output:
            assert output.split(",")[0].strip() == str(n)
        mpy_cmd = "x = (x+1 if 'x' in dir() else 1);import sys;print(x, ',', sys.platform)"
        cmd = base + ["resume", "exec", mpy_cmd]





@pytest.mark.manual
@pytest.mark.parametrize("mcu_port, ser_port", all_connected_devices())
def test_mpr_rst_no_download(capsys, ser_port: str, mcu_port: str):
    TIME_OUT = 10
    if not "esp" in mcu_port.lower():
        pytest.skip("Not an ESP device")
    device = Pyboard(ser_port)
    flush = device.serial.read_all()
    with capsys.disabled():
        t_start = time.time()
        print("\n======================================================")
        print(f"Press the reset button on {mcu_port} connected to {ser_port} and [tap the spacebar]: ")
        while 1 and (time.time() - t_start) <= TIME_OUT:
            time.sleep(0.01)
            if keyboard.is_pressed("space"):
                while keyboard.is_pressed("space"):
                    time.sleep(0.01)
                break
        print("======================================================\n")
        if (time.time() - t_start) > TIME_OUT:
            pytest.skip("No human detected.")  # need someone to press the reset button
        time.sleep(3)  # give the MCU time to reset
        output = device.serial.read_all()
        output = output.decode(errors="ignore")
        print(output)
        print("\n======================================================\n")

    # capture this
    print("\n======================================================\n")
    print(output)
    print("\n======================================================\n")

    IN_DL = [
        "DOWNLOAD_BOOT",
        "waiting for download",
        "boot mode:(1,",
        "waiting for host",
        "DOWNLOAD(USB",
    ]
    NO_DL = [
        "SPI_FAST_FLASH_BOOT",
        'Type "help()" for more information.',
        ">>>",
    ]

    # no download message detected
    assert not any(
        [msg in output for msg in IN_DL]
    ), f"Board waiting for firmware download to board.\n{output}"

    assert any([msg in output for msg in NO_DL]), f"Micropython not detected.\n{output}"
