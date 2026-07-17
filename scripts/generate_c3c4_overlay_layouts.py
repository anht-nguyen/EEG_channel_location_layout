from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.export_eeg_channel_layouts import build_info, load_montage
from scripts.figure_2_layout_common import DEFAULT_DPI, build_figure
from scripts.generate_egi_1010_region_overlay import (
    BACKGROUND_PNG_REGION_POSITIONS,
    DEFAULT_BACKGROUND_PNG,
    REGION_STYLES,
    configure_axes,
    expand_polygon,
)
from scripts.generate_figure_2_summary import FIGURE_SPECS
STANDARD_OUTPUT_DIR = REPO_ROOT / "output" / "manuscript_figure_2"
EGI_OUTPUT_DIR = REPO_ROOT / "output" / "egi_1010_equivalent_regions"

SCALP_LAYOUT_KEYS = (
    "standard_19_channel",
    "common_32_channel",
    "extended_64_channel",
)
C3C4_REGION_STYLE = {
    "fill": "#F59E0B",
    "edge": "#B45309",
    "alpha": 0.34,
    "radius": 0.020,
    "linewidth": 2.6,
}
EGI_C3C4_EQUIVALENT_REGIONS = (
    ("E41", "E36", "E30", "E42", "E37"),
    ("E105", "E104", "E103", "E87", "E93"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate four layout PNGs with transparent paired C3/C4 overlays."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Raster DPI for PNG export. Default: {DEFAULT_DPI}",
    )
    parser.add_argument(
        "--background-png",
        type=Path,
        default=DEFAULT_BACKGROUND_PNG,
        help=f"Background PNG for the EGI layout. Default: {DEFAULT_BACKGROUND_PNG}",
    )
    return parser.parse_args()


def resolve_channel_positions(fig: plt.Figure, channel_names: list[str]) -> dict[str, np.ndarray]:
    for axis in fig.axes:
        for collection in getattr(axis, "collections", []):
            if not hasattr(collection, "get_offsets"):
                continue
            offsets = collection.get_offsets()
            if len(offsets) != len(channel_names):
                continue
            return {
                channel_name: np.array(offset, dtype=float)
                for channel_name, offset in zip(channel_names, offsets)
            }
    raise RuntimeError("Could not resolve plotted channel positions from the generated figure.")


def add_c3c4_circle_overlays(ax: plt.Axes, channel_positions: dict[str, np.ndarray]) -> None:
    for channel_name in ("C3", "C4"):
        center = channel_positions[channel_name]
        ax.add_patch(
            Circle(
                tuple(center),
                radius=C3C4_REGION_STYLE["radius"],
                facecolor=C3C4_REGION_STYLE["fill"],
                edgecolor=C3C4_REGION_STYLE["edge"],
                linewidth=C3C4_REGION_STYLE["linewidth"],
                alpha=C3C4_REGION_STYLE["alpha"],
                zorder=1.5,
            )
        )


def save_png(fig: plt.Figure, output_path: Path, dpi: int) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi)
    return output_path


def export_standard_layouts(dpi: int) -> list[Path]:
    exported_paths: list[Path] = []

    for spec_key in SCALP_LAYOUT_KEYS:
        figure, _, _, _ = build_figure(spec_key, FIGURE_SPECS[spec_key], include_titles=False)
        montage = load_montage(FIGURE_SPECS[spec_key]["montage"])
        info = build_info(montage)
        channel_positions = resolve_channel_positions(figure, info.ch_names)
        add_c3c4_circle_overlays(figure.axes[0], channel_positions)

        output_path = STANDARD_OUTPUT_DIR / f"layout_{spec_key}_titleless_C3C4.png"
        save_png(figure, output_path, dpi)
        exported_paths.append(output_path)
        plt.close(figure)

    return exported_paths


def draw_egi_c3c4_overlays(ax: plt.Axes) -> None:
    for region_channels in EGI_C3C4_EQUIVALENT_REGIONS:
        points = np.array(
            [BACKGROUND_PNG_REGION_POSITIONS[channel] for channel in region_channels],
            dtype=float,
        )
        overlay_shape = expand_polygon(points, REGION_STYLES["c_pair"]["background_padding"])
        ax.add_patch(
            Polygon(
                overlay_shape,
                closed=True,
                facecolor=C3C4_REGION_STYLE["fill"],
                edgecolor=C3C4_REGION_STYLE["edge"],
                linewidth=C3C4_REGION_STYLE["linewidth"],
                alpha=C3C4_REGION_STYLE["alpha"],
                joinstyle="round",
                zorder=1.5,
            )
        )


def export_egi_layout(background_png: Path, dpi: int) -> Path:
    image = mpimg.imread(background_png)
    height, width = image.shape[:2]
    fig = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(image, extent=(0, width, height, 0))
    configure_axes(ax, (float(width), float(height)))
    draw_egi_c3c4_overlays(ax)

    output_path = EGI_OUTPUT_DIR / "layout_egi_montage_1010_equivalent_regions_C3C4.png"
    save_png(fig, output_path, dpi)
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()

    exported_paths = export_standard_layouts(args.dpi)
    exported_paths.append(export_egi_layout(args.background_png, args.dpi))

    for exported_path in exported_paths:
        print(exported_path)


if __name__ == "__main__":
    main()
