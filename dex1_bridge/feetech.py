"""Minimal Feetech STS3215 driver (SCS serial protocol on a half-duplex bus).

Only what the Dex1 bridge needs: ping, read/write registers, and a combined
position/speed/load read. Raw units are used throughout (0-4095 steps per turn).
"""

import threading

import serial

# STS3215 control table (subset)
ID = 5
TORQUE_ENABLE = 40
GOAL_POSITION = 42      # 2 bytes
PRESENT_POSITION = 56   # 2 bytes, followed by present speed (58, 2) and present load (60, 2)
PRESENT_VOLTAGE = 62    # 1 byte, 0.1 V
PRESENT_TEMPERATURE = 63  # 1 byte, deg C

_PING, _READ, _WRITE = 0x01, 0x02, 0x03

STEPS_PER_TURN = 4096

# Bits of the status error byte
ERROR_BITS = {0: "voltage", 1: "angle sensor", 2: "overheat", 3: "overcurrent", 5: "overload"}


class FeetechError(IOError):
    pass


def _signed(value, sign_bit):
    """Feetech encodes negative values as sign-magnitude."""
    if value & (1 << sign_bit):
        return -(value & ((1 << sign_bit) - 1))
    return value


def describe_error(error):
    return ", ".join(name for bit, name in ERROR_BITS.items() if error & (1 << bit)) or "none"


class STS3215:
    def __init__(self, port, motor_id, baudrate=1_000_000, timeout=0.02):
        self.id = motor_id
        self.last_error = 0
        # exclusive: a second bridge/notebook on the same port fails loudly instead of interleaving packets
        self._serial = serial.Serial(port, baudrate, timeout=timeout, exclusive=True)
        self._lock = threading.Lock()

    def close(self):
        self._serial.close()

    def _transact(self, instruction, params=b""):
        body = bytes([self.id, len(params) + 2, instruction]) + bytes(params)
        packet = b"\xff\xff" + body + bytes([~sum(body) & 0xFF])
        with self._lock:
            self._serial.reset_input_buffer()
            self._serial.write(packet)
            header = self._serial.read(4)  # 0xFF 0xFF id length
            if len(header) < 4 or header[:2] != b"\xff\xff":
                raise FeetechError(f"no reply from motor {self.id}")
            if header[2] != self.id:
                raise FeetechError(f"reply from id {header[2]}, expected {self.id}")
            rest = self._serial.read(header[3])  # error byte, data, checksum
        if len(rest) < header[3]:
            raise FeetechError(f"truncated reply from motor {self.id}")
        if (~sum(header[2:] + rest[:-1]) & 0xFF) != rest[-1]:
            raise FeetechError(f"bad checksum from motor {self.id}")
        self.last_error = rest[0]
        return rest[1:-1]

    def ping(self):
        try:
            self._transact(_PING)
            return True
        except FeetechError:
            return False

    def read(self, address, length):
        data = self._transact(_READ, bytes([address, length]))
        if len(data) != length:
            raise FeetechError(f"expected {length} bytes, got {len(data)}")
        return data

    def write(self, address, data):
        self._transact(_WRITE, bytes([address]) + bytes(data))

    def read_state(self):
        """Return (position_steps, speed_steps_per_s, load_permille) in one bus transaction."""
        data = self.read(PRESENT_POSITION, 6)
        position = _signed(int.from_bytes(data[0:2], "little"), 15)
        speed = _signed(int.from_bytes(data[2:4], "little"), 15)
        load = _signed(int.from_bytes(data[4:6], "little"), 10)
        return position, speed, load

    def read_temperature(self):
        return self.read(PRESENT_TEMPERATURE, 1)[0]

    def set_torque(self, enabled):
        self.write(TORQUE_ENABLE, [1 if enabled else 0])

    def set_goal_position(self, steps):
        self.write(GOAL_POSITION, int(steps).to_bytes(2, "little"))
