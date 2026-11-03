#!/usr/bin/env python3
"""Dex1 gripper test client: a Python port of dex1_1_service's test_dex1_1_gripper_server.

Talks only DDS, so it works the same against a real Dex1_1 or the PincOpen bridge.

  python test_dex1_sweep.py --watch          # print rt/dex1/<side>/state, send nothing
  python test_dex1_sweep.py                  # sine sweep, q = 3.0 +/- 2.5 rad over 3 s
  python test_dex1_sweep.py --q 0            # hold one position (0 = closed, 5.4 = open)
"""

import argparse
import math
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_go_msg_dds__MotorCmd_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import MotorCmds_, MotorStates_


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--side", choices=["right", "left"], default="right")
    parser.add_argument("-n", "--network", default=None, help="DDS network interface (default: auto)")
    parser.add_argument("--domain", type=int, default=0)
    parser.add_argument("--watch", action="store_true", help="only print the state, send no commands")
    parser.add_argument("--q", type=float, help="hold this position instead of sweeping")
    parser.add_argument("--center", type=float, default=3.0, help="sweep center, rad")
    parser.add_argument("--amplitude", type=float, default=2.5, help="sweep amplitude, rad")
    parser.add_argument("--period", type=float, default=3.0, help="sweep period, s")
    args = parser.parse_args()

    ChannelFactoryInitialize(args.domain, args.network)
    state_sub = ChannelSubscriber(f"rt/dex1/{args.side}/state", MotorStates_)
    state_sub.Init()

    print(f"Waiting for rt/dex1/{args.side}/state ...")
    state = None
    while state is None:
        msg = state_sub.Read(1.0)
        if msg is not None and msg.states:
            state = msg.states[0]
    print(f"{args.side} gripper at q = {state.q:.3f}")

    cmd_pub = None
    if not args.watch:
        cmd_pub = ChannelPublisher(f"rt/dex1/{args.side}/cmd", MotorCmds_)
        cmd_pub.Init()
        cmd = MotorCmds_(cmds=[unitree_go_msg_dds__MotorCmd_()])
        cmd.cmds[0].mode = 1
        cmd.cmds[0].kp = 5.0
        cmd.cmds[0].kd = 0.05

    # start the sine at the current position, like the C++ test
    phase = math.asin(max(-1.0, min(1.0, (state.q - args.center) / args.amplitude)))
    t0 = time.monotonic() - phase * args.period / (2 * math.pi)

    try:
        while True:
            msg = state_sub.Read(0.0)
            if msg is not None and msg.states:
                state = msg.states[0]
            line = f"\rq={state.q:6.3f} dq={state.dq:7.3f} tau={state.tau_est:6.3f} lost={state.lost}"
            if cmd_pub is not None:
                if args.q is not None:
                    q = args.q
                else:
                    q = args.center + args.amplitude * math.sin(2 * math.pi * (time.monotonic() - t0) / args.period)
                cmd.cmds[0].q = q
                cmd_pub.Write(cmd)
                line += f"  cmd={q:6.3f}"
            print(line, end="", flush=True)
            time.sleep(0.005)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
