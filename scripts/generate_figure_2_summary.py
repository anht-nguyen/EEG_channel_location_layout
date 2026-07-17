from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.eeg_config import EEG_32_CHANNELS, EEG_64_CHANNELS
from scripts.figure_2_layout_common import (
    COLORS,
    CONSISTENT_SCALP_VIEW_BOUNDS,
    DEFAULT_DPI,
    DEFAULT_FORMATS,
    DEFAULT_OUTPUT_DIR,
    export_spec,
    write_manifest,
)


STANDARD_19_CHANNELS = [
    "Fp1",
    "Fp2",
    "F7",
    "F3",
    "Fz",
    "F4",
    "F8",
    "T7",
    "C3",
    "Cz",
    "C4",
    "T8",
    "P7",
    "P3",
    "Pz",
    "P4",
    "P8",
    "O1",
    "O2",
]

STANDARD_19_LABEL_STYLE = {"fontsize": 18}
COMMON_32_LABEL_STYLE = {"fontsize": 18}
EXTENDED_64_LABEL_STYLE = {"fontsize": 15}

FIGURE_SPECS = {
    "standard_19_channel": {
        "title": "Standard 10-20 / 10-20-derived layout",
        "subtitle": "Representative common 19-channel whole-head montage",
        "montage": "standard_1020",
        "channel_list": STANDARD_19_CHANNELS,
        "label_names": STANDARD_19_CHANNELS,
        "sphere": "eeglab",
        "visible_style": {
            "facecolor": COLORS["highlight_fill"],
            "edgecolor": COLORS["highlight_edge"],
        },
        "label_style": STANDARD_19_LABEL_STYLE,
        "show_context": False,
        "fixed_view_bounds": CONSISTENT_SCALP_VIEW_BOUNDS,
    },
    "common_32_channel": {
        "title": "Common 32-channel layout",
        "subtitle": "Representative 32-channel whole-head montage",
        "montage": "easycap-M1",
        "channel_list": EEG_32_CHANNELS,
        "label_names": EEG_32_CHANNELS,
        "sphere": "eeglab",
        "visible_style": {
            "facecolor": COLORS["highlight_fill"],
            "edgecolor": COLORS["highlight_edge"],
        },
        "label_style": COMMON_32_LABEL_STYLE,
        "show_context": False,
        "fixed_view_bounds": CONSISTENT_SCALP_VIEW_BOUNDS,
    },
    "extended_64_channel": {
        "title": "10-10 montage layout (64 channels)",
        "subtitle": "Representative 64-channel extended central montage",
        "montage": "standard_1005",
        "channel_list": EEG_64_CHANNELS,
        "label_names": EEG_64_CHANNELS,
        "sphere": "eeglab",
        "visible_style": {
            "facecolor": COLORS["highlight_fill"],
            "edgecolor": COLORS["highlight_edge"],
        },
        "label_style": EXTENDED_64_LABEL_STYLE,
        "show_context": False,
        "fixed_view_bounds": CONSISTENT_SCALP_VIEW_BOUNDS,
    },
    "high_density_128_channel": {
        "title": "Geodesic 400 128-channel EEG montage",
        "subtitle": "Representative higher-density whole-head geodesic array",
        "montage": "GSN-HydroCel-128",
        "channel_list": None,
        "label_names": [],
        "sphere": None,
        "visible_style": {
            "facecolor": COLORS["highlight_fill"],
            "edgecolor": COLORS["highlight_edge"],
        },
        "show_context": False,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export single-layout EEG montage figures for manuscript Figure 2."
    )
    parser.add_argument(
        "--figures",
        nargs="+",
        choices=list(FIGURE_SPECS),
        default=list(FIGURE_SPECS),
        help="One or more figure specs to export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for exported figure files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["png", "svg", "pdf"],
        default=DEFAULT_FORMATS,
        help="One or more output formats.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Raster DPI for PNG export. Default: {DEFAULT_DPI}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exported_specs: list[tuple[str, list[Path], Path]] = []

    for spec_key in args.figures:
        figure_paths, summary_path = export_spec(
            spec_key,
            FIGURE_SPECS[spec_key],
            output_dir=args.output_dir,
            formats=args.formats,
            dpi=args.dpi,
        )
        exported_specs.append((spec_key, figure_paths, summary_path))

    manifest_path = write_manifest(
        args.output_dir,
        exported_specs,
        manifest_name="figure_2_single_layouts_manifest.txt",
    )

    for spec_key, figure_paths, summary_path in exported_specs:
        print(f"Exported {spec_key}:")
        for figure_path in figure_paths:
            print(f"  figure={figure_path}")
        print(f"  summary={summary_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
