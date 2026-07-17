from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.figure_2_layout_common import (
    COLORS,
    DEFAULT_DPI,
    DEFAULT_FORMATS,
    DEFAULT_OUTPUT_DIR,
    export_spec,
    write_manifest,
)


SPEC_KEY = "coverage_tiers"
PANEL_B_CORE = ["C3", "Cz", "C4"]
PANEL_B_ADJACENT = [
    "FC3",
    "FC4",
    "FC1",
    "FC2",
    "C1",
    "C2",
    "C5",
    "C6",
    "CP3",
    "CP4",
    "CP1",
    "CP2",
]
PANEL_B_OCCASIONAL = [
    "Fp1",
    "Fp2",
    "F3",
    "F4",
    "F7",
    "Fz",
    "T7",
    "P3",
    "P4",
    "O1",
    "O2",
    "FC5",
    "FC6",
    "CP5",
    "CP6",
]
PANEL_B_LABELS = PANEL_B_CORE + PANEL_B_ADJACENT + PANEL_B_OCCASIONAL

COVERAGE_TIER_SPEC = {
    "title": "Electrode coverage summary",
    "subtitle": "10-10 montage template with core, adjacent, and occasional tiers",
    "montage": "standard_1010",
    "channel_list": None,
    "label_names": PANEL_B_LABELS,
    "label_style": {
        "fontsize": 16,
        "fontweight": "medium",
        "color": COLORS["text"],
    },
    "figure_size": (12.5, 8),
    "sphere": "eeglab",
    "visible_style": {
        "facecolor": COLORS["context_fill"],
        "edgecolor": COLORS["context_edge"],
        "markersize": 42,
        "linewidth": 1.4,
    },
    "show_context": True,
    "legend_style": {
        "loc": "lower left",
        "bbox_to_anchor": (-0.22, 0.035),
        "fontsize": 16,
        "markersize": 12,
    },
    "group_styles": [
        {
            "label": "Core sensorimotor",
            "names": PANEL_B_CORE,
            "facecolor": COLORS["core_fill"],
            "edgecolor": COLORS["outline"],
            "markersize": 92,
            "linewidth": 1.9,
        },
        {
            "label": "Recurring adjacent",
            "names": PANEL_B_ADJACENT,
            "facecolor": COLORS["adjacent_fill"],
            "edgecolor": COLORS["outline"],
            "markersize": 80,
            "linewidth": 1.8,
        },
        {
            "label": "Occasional peripheral/comparison",
            "names": PANEL_B_OCCASIONAL,
            "facecolor": COLORS["occasional_fill"],
            "edgecolor": COLORS["outline"],
            "markersize": 72,
            "linewidth": 1.7,
        },
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export coverage-tier EEG montage figures and summary files."
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
    figure_paths, summary_path = export_spec(
        SPEC_KEY,
        COVERAGE_TIER_SPEC,
        output_dir=args.output_dir,
        formats=args.formats,
        dpi=args.dpi,
    )
    manifest_path = write_manifest(
        args.output_dir,
        [(SPEC_KEY, figure_paths, summary_path)],
        manifest_name="coverage_tiers_manifest.txt",
    )

    print(f"Exported {SPEC_KEY}:")
    for figure_path in figure_paths:
        print(f"  figure={figure_path}")
    print(f"  summary={summary_path}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
