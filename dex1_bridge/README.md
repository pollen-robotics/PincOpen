# PincOpen as a Unitree Dex1_1

`pincopen_dex1_server.py` makes a PincOpen gripper speak the same DDS interface as Unitree's
[dex1_1_service](https://github.com/unitreerobotics/dex1_1_service), so Dex1 clients
(`xr_teleoperate --ee dex1`, unitree_IL_lerobot, ...) drive it without changes.

| | Topic | Type | Fields used |
|---|---|---|---|
| command | `rt/dex1/<side>/cmd` | `unitree_go MotorCmds_` | `cmds[0].q` |
| state | `rt/dex1/<side>/state` | `unitree_go MotorStates_` | `q`, `dq`, `tau_est`, `q_raw`, `lost` |

- `q` uses Dex1 units: `0` = closed, `5.4` rad = fully open. Commands outside that range are clamped.
- `kp`, `kd`, `dq`, `tau` are ignored; the STS3215 runs its own position loop.
- No command for 1 s → the gripper holds its current position (the Dex1 service brakes).
- Ctrl+C turns torque off.
- `tau_est` is the Feetech load scaled to the STS3215 stall torque, so it's approximate.

## Install

`cyclonedds==0.10.2` only ships macOS arm64 wheels up to Python 3.10:

```bash
uv venv --python 3.10 .venv-dex1
uv pip install --python .venv-dex1/bin/python pyserial \
  "unitree_sdk2py @ git+https://github.com/unitreerobotics/unitree_sdk2_python.git"
```

## Test

The quickest way is [`notebooks/dex1_bridge_tests.ipynb`](../notebooks/dex1_bridge_tests.ipynb) (kernel
"PincOpen Dex1 (py3.10)"): it runs the bridge in-process and checks the motor, calibration and
the full DDS interface. The steps below do the same from two terminals.

From a terminal, activate the environment first (`source .venv-dex1/bin/activate` from the repo
root) and close any notebook/kernel that has the serial port open: the bridge locks the port.

1. **Calibrate** (torque off, you move the gripper by hand). Writes `calibration.json`:
   ```bash
   python pincopen_dex1_server.py --calibrate --motor-id 7
   ```
2. **State only.** Start the server, then in a second terminal watch the state while moving the
   fingers by hand. Torque stays off until a command arrives:
   ```bash
   python pincopen_dex1_server.py --side right
   python test_dex1_sweep.py --watch
   ```
   Expect `q ≈ 0` closed and `q ≈ 5.4` open.
3. **Motion.** With the server running:
   ```bash
   python test_dex1_sweep.py --q 2.7   # move to half open and hold
   python test_dex1_sweep.py           # Unitree's sine sweep, q = 0.5..5.5 rad
   ```
4. **On the robot.** Run the server on a machine on the robot network with `--network eth0`
   (motor ID 0 is `right`, 1 is `left` on a real Dex1; here the side is just `--side`), then start
   `xr_teleoperate` with `--ee dex1`.

If the two processes don't see each other on a Mac, pass the same interface to both, e.g.
`-n en0` (or `-n lo0`).
