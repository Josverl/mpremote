import time
import pytest
import subprocess
import serial.tools.list_ports

# @pytest.fixture
def all_devices():
    # List attached devices.
    devices = [p.device for p in serial.tools.list_ports.comports()]
    return sorted(devices)

@pytest.mark.parametrize("port", all_devices())
def test_mpremote_no_reset_disconnect(port):
    """
    Validate that mpremote does not issue a hard reset when terminating a session
    Requires that the MCU device does not have a 'main.py' file that runs in a loop.
    """
    mpy_cmd = "x = (x+1 if 'x' in dir() else 1);import sys;print(x, ',', sys.platform)"
    if port:
        base = ["mpremote","connect",port, "resume"]
    else:
        base = ["mpremote", "resume"]
    # initial hard reset
    spr = subprocess.run(base + ["reset"], capture_output=True)
    output = spr.stdout.decode("utf-8")
    if "no device found" in output:
        pytest.skip("no device found")
    if "failed to access" in output:
        pytest.skip(output)
    assert spr.returncode == 0
    # allow 2 secs for MCU hard reset to complete
    time.sleep(2)
    cmd = base + ["resume", "exec", mpy_cmd]
    for n in range(1,4):
        spr = subprocess.run(cmd, capture_output=True)
        assert spr.returncode == 0
        output = spr.stdout.decode("utf-8")
        print(f"Port {port}, Test {n} : {output}")
        if ',' in output:
            assert output.split(',')[0].strip() == str(n)








