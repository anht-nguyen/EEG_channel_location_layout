from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

local_mne_home = REPO_ROOT / ".mne"
os.environ.setdefault("MNE_HOME", str(local_mne_home))
os.environ["USERPROFILE"] = str(REPO_ROOT)
os.environ["APPDATA"] = str(REPO_ROOT)
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mne

from config.eeg_config import DEFAULT_MONTAGE, DEFAULT_OUTPUT_DIR, USE_MONTAGE_NATIVE_CHANNELS


BUILTIN_MONTAGES = tuple(mne.channels.get_builtin_montages())
DEFAULT_OUTPUT_PATH = REPO_ROOT / DEFAULT_OUTPUT_DIR


def load_montage(source_name: str) -> mne.channels.DigMontage:
    return mne.channels.make_standard_montage(source_name)


def build_summary_lines(layout_name: str, info: mne.Info) -> list[str]:
    return [
        f"layout={layout_name}",
        f"channels_found={len(info.ch_names)}",
        "channels=" + ",".join(info.ch_names),
        "missing_channels=",
        "exported_figures=yes",
    ]


def build_info(montage: mne.channels.DigMontage) -> mne.Info:
    channel_names = list(montage.get_positions()["ch_pos"].keys())
    info = mne.create_info(ch_names=channel_names, sfreq=256.0, ch_types="eeg")
    info.set_montage(montage, on_missing="ignore")
    return info


def export_2d_figure(info: mne.Info, title: str, output_path: Path) -> None:
    fig = mne.viz.plot_sensors(
        info,
        kind="topomap",
        show_names=True,
        show=False,
    )
    fig.set_size_inches(10, 8)
    fig.suptitle(title)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def export_3d_figure(info: mne.Info, title: str, output_path: Path) -> None:
    fig = mne.viz.plot_sensors(
        info,
        kind="3d",
        show_names=True,
        show=False,
    )
    fig.set_size_inches(10, 8)
    if fig.axes:
        fig.axes[0].set_title(title)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def export_layout_figures(output_dir: Path, layouts: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for layout_name in layouts:
        montage = load_montage(layout_name)
        summary_path = output_dir / f"{layout_name}_summary.txt"
        info = build_info(montage)
        title_suffix = f" ({len(info.ch_names)} channels)"

        export_2d_figure(
            info=info,
            title=f"{layout_name} 2D{title_suffix}",
            output_path=output_dir / f"{layout_name}_2d.png",
        )
        export_3d_figure(
            info=info,
            title=f"{layout_name} 3D{title_suffix}",
            output_path=output_dir / f"{layout_name}_3d.png",
        )

        summary_path.write_text(
            "\n".join(build_summary_lines(layout_name, info)) + "\n",
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export EEG channel layout figures for the configured EEG channel list."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Directory for exported figures. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--layouts",
        nargs="+",
        choices=sorted(BUILTIN_MONTAGES),
        default=list(BUILTIN_MONTAGES),
        help="One or more built-in MNE montages to export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_layout_figures(output_dir=args.output_dir, layouts=args.layouts)
    print(f"Exported channel layout figures to: {args.output_dir}")
    print(f"Reference montage in config: {DEFAULT_MONTAGE}")
    print(f"Use montage native channels: {USE_MONTAGE_NATIVE_CHANNELS}")


if __name__ == "__main__":
    main()
