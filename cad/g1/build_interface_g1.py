"""Build Interface_G1: the Pinc'Open adapter for the Unitree G1 wrist (EDU / Flagship).

The part has two halves:
  * the G1 plug: the body that goes into the wrist clamp. It is taken unchanged from
    lerobot's `unitree-g1-openarm-adapter.stl` (vendor/), the only plug geometry known
    to fit a real G1. Its OpenArm plate is dropped.
  * the Pinc'Open plate, modelled here in CadQuery: a 56 mm disc, 8 mm thick, with
    the 4-screw pattern of `cad/step/Interface_ARM100.step` (44 x 11.2 mm, 2.5 mm
    thermoplastic screws, heads recessed from the plug side).

Outputs (all in the plug's STL frame, mm):
  cad/step/Interface_G1_Plate.step   editable STEP of the plate
  cad/stl/Interface_G1.stl           printable plug + plate
  assets/images/g1_interface_drawing.png  (with --drawing)

Frame of the plug STL: +Y points out of the wrist, toward the gripper. X is the
plug's 28 mm side, which lies along the G1 wrist Y axis, the axis the Dex1-1 jaws
travel on. Z is the plug's 49.6 mm side.

Usage (from the repo root):
  uv venv --python 3.11 .venv-cad
  uv pip install --python .venv-cad/bin/python cadquery trimesh manifold3d networkx scipy shapely matplotlib
  .venv-cad/bin/python cad/g1/build_interface_g1.py [--drawing] [--jaw-axis plug_short|plug_long]
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

REPO = Path(__file__).resolve().parents[2]
PLUG_STL = REPO / "cad/g1/vendor/unitree-g1-openarm-adapter.stl"
OUT_STEP = REPO / "cad/step/Interface_G1_Plate.step"
OUT_STL = REPO / "cad/stl/Interface_G1.stl"
OUT_DRAWING = REPO / "assets/images/g1_interface_drawing.png"

# --- G1 plug (measured from the vendored STL) ---------------------------------
SEAT_Y = 16.5  # face of the plug that seats on the wrist; the OpenArm plate starts here
DISC_CENTER = (3.14, -0.20)  # (x, z) centre of the original 56 mm plate
PATTERN_CENTER = (3.085, -0.37)  # (x, z) centre of the original OpenArm hole square

# --- Pinc'Open plate (from Interface_ARM100.step) -----------------------------
DISC_DIA = 56.0
PLATE_T = 8.0
HOLE_SPAN = (44.0, 11.2)  # along the jaw axis, across it
HOLE_DIA = 2.5  # clearance for 2.5 mm thermoplastic screws
CBORE_DIA = 6.5
CBORE_DEPTH = 6.0  # leaves 2.0 mm under the head, as on ARM100 -> 2.5x8 screws
MIN_ACCESS_CLEARANCE = 1.0  # counterbore edge to plug footprint, mm


def hole_centers(jaw_axis: str) -> list[tuple[float, float]]:
    along, across = HOLE_SPAN
    dx, dz = (along / 2, across / 2) if jaw_axis == "plug_short" else (across / 2, along / 2)
    cx, cz = PATTERN_CENTER
    return [(cx + sx * dx, cz + sz * dz) for sx in (-1, 1) for sz in (-1, 1)]


def load_plug() -> trimesh.Trimesh:
    """Plug bodies below the seat face, unioned into one solid."""
    mesh = trimesh.load(PLUG_STL)
    bodies = [b for b in mesh.split(only_watertight=False) if b.volume > 1.0 and b.bounds[1, 1] <= SEAT_Y + 0.01]
    if len(bodies) != 2:
        sys.exit(f"expected 2 plug bodies below y={SEAT_Y}, found {len(bodies)}: has the vendored STL changed?")
    return trimesh.boolean.union(bodies, engine="manifold")


def check_access(plug: trimesh.Trimesh, holes: list[tuple[float, float]]) -> None:
    """Screws go in from the plug side, so each counterbore must sit outside the plug footprint."""
    (x0, _, z0), (x1, _, z1) = plug.bounds
    r = CBORE_DIA / 2
    for x, z in holes:
        gap = max(x0 - (x + r), (x - r) - x1, z0 - (z + r), (z - r) - z1)
        if gap < MIN_ACCESS_CLEARANCE:
            sys.exit(
                f"counterbore at x={x:.1f}, z={z:.1f} is {gap:.1f} mm from the plug footprint "
                f"(need {MIN_ACCESS_CLEARANCE} mm): the screw can't be reached. "
                "This jaw orientation needs access bores through the plug; see docs/g1_wrist_interface.md."
            )


def build_plate(holes: list[tuple[float, float]]) -> cq.Workplane:
    # Workplane "XZ" has its normal along -Y, so extrude negative to grow toward +Y.
    # Its local axes are (X, Z) -> (x, z) of the plug frame.
    wp = cq.Workplane("XZ", origin=(0, SEAT_Y, 0))
    plate = wp.center(*DISC_CENTER).circle(DISC_DIA / 2).extrude(-PLATE_T)
    pts = [(x - DISC_CENTER[0], z - DISC_CENTER[1]) for x, z in holes]
    bores = (
        cq.Workplane("XZ", origin=(0, SEAT_Y, 0)).center(*DISC_CENTER).pushPoints(pts)
        .circle(CBORE_DIA / 2).extrude(-CBORE_DEPTH)
    )
    shanks = (
        cq.Workplane("XZ", origin=(0, SEAT_Y, 0)).center(*DISC_CENTER).pushPoints(pts)
        .circle(HOLE_DIA / 2).extrude(-PLATE_T)
    )
    return plate.cut(bores).cut(shanks)


def draw(plug: trimesh.Trimesh, holes: list[tuple[float, float]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    (x0, y0, z0), (x1, _, z1) = plug.bounds
    fig, (ax, side) = plt.subplots(1, 2, figsize=(11, 5.5), gridspec_kw={"width_ratios": [1.1, 1]})

    ax.set_title("Seat face, seen from the wrist (plug side)")
    ax.add_patch(Circle(DISC_CENTER, DISC_DIA / 2, fill=False, lw=1.5))
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, color="0.85", label="G1 plug footprint"))
    for x, z in holes:
        ax.add_patch(Circle((x, z), CBORE_DIA / 2, fill=False, color="C3"))
        ax.add_patch(Circle((x, z), HOLE_DIA / 2, color="C3"))
    (ha, hb), (hc, hd) = holes[0], holes[3]
    ax.annotate("", (ha, hb - 6), (hc, hb - 6), arrowprops=dict(arrowstyle="<->"))
    ax.text((ha + hc) / 2, hb - 8.5, f"{HOLE_SPAN[0]:.1f}", ha="center")
    ax.annotate("", (hc + 5, hb), (hc + 5, hd), arrowprops=dict(arrowstyle="<->"))
    ax.text(hc + 6, (hb + hd) / 2, f"{HOLE_SPAN[1]:.1f}", va="center")
    ax.text(x0 + 1, z1 - 4, f"{x1 - x0:.1f} x {z1 - z0:.1f}", fontsize=8)
    ax.text(DISC_CENTER[0], DISC_CENTER[1] - DISC_DIA / 2 - 4, f"Ø{DISC_DIA:.0f} x {PLATE_T:.0f} plate", ha="center")
    ax.text(DISC_CENTER[0], DISC_CENTER[1] + DISC_DIA / 2 + 2,
            f"4x Ø{HOLE_DIA} through, Ø{CBORE_DIA} cbore {CBORE_DEPTH:.0f} deep", ha="center", color="C3")
    ax.set_xlabel("x (mm): plug 28 mm side = jaw travel (wrist Y, as Dex1-1)")
    ax.set_ylabel("z (mm): plug 49.6 mm side")
    ax.set_aspect("equal")
    ax.set_xlim(DISC_CENTER[0] - 34, DISC_CENTER[0] + 34)
    ax.set_ylim(DISC_CENTER[1] - 36, DISC_CENTER[1] + 36)
    ax.legend(loc="lower left", fontsize=8)

    side.set_title("Side view (section through the screws)")
    side.add_patch(Rectangle((x0, y0), x1 - x0, SEAT_Y - y0, color="0.85"))
    side.add_patch(Rectangle((DISC_CENTER[0] - DISC_DIA / 2, SEAT_Y), DISC_DIA, PLATE_T, fill=False, lw=1.5))
    for x in sorted({h[0] for h in holes}):
        side.add_patch(Rectangle((x - CBORE_DIA / 2, SEAT_Y), CBORE_DIA, CBORE_DEPTH, color="C3", alpha=0.35))
        side.add_patch(Rectangle((x - HOLE_DIA / 2, SEAT_Y), HOLE_DIA, PLATE_T, color="C3"))
    side.text(DISC_CENTER[0], SEAT_Y + PLATE_T + 1.5, "Pinc'Open back face (Top/Bottom_Plate)", ha="center", fontsize=8)
    side.text(DISC_CENTER[0], (y0 + SEAT_Y) / 2, "G1 plug\n(into wrist clamp)", ha="center", va="center", fontsize=8)
    side.text(x1 + 1, SEAT_Y - 1, f"seat face\ny={SEAT_Y}", fontsize=8, va="top")
    side.set_xlabel("x (mm)")
    side.set_ylabel("y (mm): out of the wrist")
    side.set_aspect("equal")
    side.set_xlim(DISC_CENTER[0] - 32, DISC_CENTER[0] + 42)
    side.set_ylim(y0 - 3, SEAT_Y + PLATE_T + 6)
    side.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jaw-axis", choices=["plug_short", "plug_long"], default="plug_short",
                    help="plug side the jaws travel along (default plug_short = like the Dex1-1)")
    ap.add_argument("--drawing", action="store_true", help=f"also write {OUT_DRAWING.relative_to(REPO)}")
    args = ap.parse_args()

    holes = hole_centers(args.jaw_axis)
    plug = load_plug()
    check_access(plug, holes)

    plate = build_plate(holes)
    cq.exporters.export(plate, str(OUT_STEP))
    with tempfile.TemporaryDirectory() as tmp:
        plate_stl = Path(tmp) / "plate.stl"
        cq.exporters.export(plate, str(plate_stl), tolerance=0.01, angularTolerance=0.05)
        plate_mesh = trimesh.load(plate_stl)

    part = trimesh.boolean.union([plug, plate_mesh], engine="manifold")
    if not part.is_watertight or part.body_count != 1:
        sys.exit(f"merged part is not one watertight solid (bodies={part.body_count})")
    part.export(OUT_STL)

    size = part.bounds[1] - part.bounds[0]
    print(f"wrote {OUT_STEP.relative_to(REPO)} and {OUT_STL.relative_to(REPO)}")
    print(f"size {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm, volume {part.volume / 1000:.1f} cm^3")
    if args.drawing:
        draw(plug, holes, OUT_DRAWING)
        print(f"wrote {OUT_DRAWING.relative_to(REPO)}")


if __name__ == "__main__":
    main()
