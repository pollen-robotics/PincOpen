#!/usr/bin/env python3
"""PincOpen <-> Unitree Dex1_1 DDS bridge.

Makes a PincOpen gripper (Feetech STS3215) look like a Unitree Dex1_1 gripper on
DDS, so clients written for the Dex1 (xr_teleoperate, unitree_IL_lerobot, ...)
can drive it unchanged. It mirrors unitreerobotics/dex1_1_service:

  subscribes  rt/dex1/<side>/cmd    unitree_go MotorCmds_    (cmds[0].q)
  publishes   rt/dex1/<side>/state  unitree_go MotorStates_  (states[0].q, dq, tau_est)

Position units follow the Dex1: q = 0 rad is closed, q = 5.4 rad is fully open.
kp, kd, dq and tau in the command are ignored (the STS3215 runs its own
position loop). When no command arrives for 1 s the gripper holds its current
position, like the Dex1 service switching to brake mode.

Usage:
  python pincopen_dex1_server.py --calibrate            # once, gripper torque off
  python pincopen_dex1_server.py --side right           # serve on DDS
"""

import argparse
import json
import logging
import pathlib
import signal
import threading
import time

from feetech import STS3215, FeetechError, describe_error

Q_OPEN = 5.4  # Dex1 travel from closed to fully open, in rad (xr_teleoperate LEFT_MAPPED_MAX)
CMD_TIMEOUT_S = 1.0  # same as dex1_1_service's SubscriptionBase timeout
STALL_TORQUE_NM = 2.94  # STS3215 at 12 V (30 kg.cm); only used to scale tau_est
DEFAULT_PORT = "/dev/cu.usbmodem58CD1773071"
DEFAULT_CALIBRATION = pathlib.Path(__file__).with_name("calibration.json")

log = logging.getLogger("pincopen_dex1")


class Calibration:
    """Linear map between Feetech steps and Dex1 q (0 = closed, Q_OPEN = open)."""

    def __init__(self, closed_raw, open_raw, motor_id):
        if abs(closed_raw - open_raw) < 200:
            raise ValueError(f"closed ({closed_raw}) and open ({open_raw}) positions are too close")
        if not (0 <= closed_raw < 4096 and 0 <= open_raw < 4096):
            raise ValueError("raw positions must be within 0..4095 (travel must not cross the wraparound)")
        self.closed_raw = closed_raw
        self.open_raw = open_raw
        self.motor_id = motor_id
        self._steps_per_rad = (open_raw - closed_raw) / Q_OPEN  # negative when opening decreases steps

    @classmethod
    def load(cls, path):
        data = json.loads(pathlib.Path(path).read_text())
        return cls(data["closed_raw"], data["open_raw"], data["motor_id"])

    def save(self, path):
        data = {"motor_id": self.motor_id, "closed_raw": self.closed_raw, "open_raw": self.open_raw}
        pathlib.Path(path).write_text(json.dumps(data, indent=2) + "\n")

    def q_from_raw(self, raw):
        return (raw - self.closed_raw) / self._steps_per_rad

    def raw_from_q(self, q):
        q = min(max(q, 0.0), Q_OPEN)
        return round(self.closed_raw + q * self._steps_per_rad)

    def dq_from_speed(self, steps_per_s):
        return steps_per_s / self._steps_per_rad


def calibrate(args):
    motor_id = args.motor_id
    if motor_id is None:
        try:
            motor_id = Calibration.load(args.calibration).motor_id  # recalibrating: keep the known id
        except (OSError, KeyError, ValueError):
            motor_id = 6  # PincOpen / SO-ARM100 convention
    motor = STS3215(args.port, motor_id)
    if not motor.ping():
        raise SystemExit(f"No motor answering on id {motor_id} at {args.port}")
    motor.set_torque(False)
    input("Torque is off. Close the gripper fully by hand, then press Enter...")
    closed_raw = motor.read_state()[0]
    input("Now open the gripper fully by hand, then press Enter...")
    open_raw = motor.read_state()[0]
    motor.close()
    calibration = Calibration(closed_raw, open_raw, motor_id)
    calibration.save(args.calibration)
    print(f"closed_raw={closed_raw} open_raw={open_raw} -> saved to {args.calibration}")


class Bridge:
    def __init__(self, motor, calibration, side, rate_hz):
        from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
        from unitree_sdk2py.idl.default import unitree_go_msg_dds__MotorState_
        from unitree_sdk2py.idl.unitree_go.msg.dds_ import MotorCmds_, MotorStates_

        self.motor = motor
        self.cal = calibration
        self.period = 1.0 / rate_hz
        self.running = True

        self._cmd_lock = threading.Lock()
        self._cmd_q = None
        self._cmd_time = 0.0

        self.state_msg = MotorStates_(states=[unitree_go_msg_dds__MotorState_()])
        self.state_pub = ChannelPublisher(f"rt/dex1/{side}/state", MotorStates_)
        self.state_pub.Init()
        self.cmd_sub = ChannelSubscriber(f"rt/dex1/{side}/cmd", MotorCmds_)
        self.cmd_sub.Init(self._on_cmd, 10)
        log.info("DDS topics: rt/dex1/%s/cmd -> motor %d -> rt/dex1/%s/state", side, motor.id, side)

    def _on_cmd(self, msg):
        if not msg.cmds:
            return
        with self._cmd_lock:
            self._cmd_q = msg.cmds[0].q
            self._cmd_time = time.monotonic()

    def _latest_cmd(self):
        with self._cmd_lock:
            if self._cmd_q is None or time.monotonic() - self._cmd_time > CMD_TIMEOUT_S:
                return None
            return self._cmd_q

    def run(self):
        torque_on = False
        holding = True
        last_goal = None
        lost = 0
        last_error = 0
        next_tick = time.monotonic()

        while self.running:
            try:
                raw, speed, load = self.motor.read_state()
            except FeetechError as e:
                lost += 1
                if lost % 100 == 1:
                    log.warning("motor read failed (%s), %d lost so far", e, lost)
                next_tick = self._sleep(next_tick)
                continue

            if self.motor.last_error != last_error:
                last_error = self.motor.last_error
                if last_error:
                    log.warning("motor status: %s", describe_error(last_error))

            q_cmd = self._latest_cmd()
            try:
                if q_cmd is not None:
                    goal = self.cal.raw_from_q(q_cmd)
                    if not torque_on:
                        self.motor.set_goal_position(raw)  # avoid a jump to a stale goal register
                        self.motor.set_torque(True)
                        torque_on = True
                        log.info("first command received, torque on")
                    if holding:
                        log.info("following commands")
                        holding = False
                    if goal != last_goal:
                        self.motor.set_goal_position(goal)
                        last_goal = goal
                elif torque_on and not holding:
                    self.motor.set_goal_position(raw)
                    last_goal = raw
                    holding = True
                    log.info("no command for %.1f s, holding position", CMD_TIMEOUT_S)
            except FeetechError as e:
                lost += 1
                log.warning("motor write failed: %s", e)

            state = self.state_msg.states[0]
            state.q = self.cal.q_from_raw(raw)
            state.dq = self.cal.dq_from_speed(speed)
            state.tau_est = load / 1000.0 * STALL_TORQUE_NM
            state.q_raw = float(raw)
            state.lost = lost
            self.state_pub.Write(self.state_msg)

            next_tick = self._sleep(next_tick)

    def _sleep(self, next_tick):
        next_tick += self.period
        delay = next_tick - time.monotonic()
        if delay > 0:
            time.sleep(delay)
            return next_tick
        return time.monotonic()  # running late: don't try to catch up


def serve(args):
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize

    calibration = Calibration.load(args.calibration)
    motor_id = args.motor_id if args.motor_id is not None else calibration.motor_id
    motor = STS3215(args.port, motor_id)
    if not motor.ping():
        raise SystemExit(f"No motor answering on id {motor_id} at {args.port}")
    log.info("motor %d on %s, %d C, calibration closed=%d open=%d",
             motor_id, args.port, motor.read_temperature(), calibration.closed_raw, calibration.open_raw)

    ChannelFactoryInitialize(args.domain, args.network)
    bridge = Bridge(motor, calibration, args.side, args.rate)

    def stop(*_):
        bridge.running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    log.info("PincOpen Dex1 server started (Ctrl+C to stop)")
    try:
        bridge.run()
    finally:
        try:
            motor.set_torque(False)
            log.info("torque off")
        except FeetechError:
            pass
        motor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", default=DEFAULT_PORT, help="Feetech adapter serial port")
    parser.add_argument("--motor-id", type=int, help="Feetech id (default: from the calibration file)")
    parser.add_argument("--side", choices=["right", "left"], default="right", help="Dex1 topic side")
    parser.add_argument("-n", "--network", default=None, help="DDS network interface, e.g. eth0 (default: auto)")
    parser.add_argument("--domain", type=int, default=0, help="DDS domain id (0 = real robot, 1 = Unitree sim)")
    parser.add_argument("--rate", type=float, default=200.0, help="control/state loop rate in Hz")
    parser.add_argument("--calibration", default=DEFAULT_CALIBRATION, help="calibration JSON path")
    parser.add_argument("-c", "--calibrate", action="store_true", help="record closed/open positions and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.calibrate:
        calibrate(args)
    else:
        serve(args)


if __name__ == "__main__":
    main()
