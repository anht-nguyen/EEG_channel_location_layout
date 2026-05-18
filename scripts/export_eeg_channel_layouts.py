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
import numpy as np

from config.eeg_config import DEFAULT_MONTAGE, EXPORT_CASES


BUILTIN_MONTAGES = tuple(mne.channels.get_builtin_montages())
EEG_POSITIONS_SYSTEM_MAP = {
    "standard_1020": "1020",
    "standard_1010": "1010",
    "standard_1005": "1005",
}


def resolve_case_layouts(case_config: dict) -> list[str]:
    montage = case_config["montage"]
    if montage == "all_builtin":
        return list(BUILTIN_MONTAGES)
    if isinstance(montage, (list, tuple)):
        return list(montage)
    return [montage]


def load_montage(montage_name: str) -> mne.channels.DigMontage:
    if montage_name in EEG_POSITIONS_SYSTEM_MAP:
        try:
            from eeg_positions import get_elec_coords
        except ImportError as exc:
            raise ImportError(
                f"Montage '{montage_name}' is configured to use eeg_positions. "
                "Install it with: python -m pip install --upgrade eeg_positions"
            ) from exc

        return get_elec_coords(
            system=EEG_POSITIONS_SYSTEM_MAP[montage_name],
            as_mne_montage=True,
        )
    return mne.channels.make_standard_montage(montage_name)


def subset_montage(
    montage: mne.channels.DigMontage,
    channel_list: list[str] | None,
) -> tuple[mne.channels.DigMontage, list[str]]:
    if channel_list is None:
        return montage, []

    positions = montage.get_positions()
    ch_pos = positions["ch_pos"]
    lookup = {
        name.casefold(): (name, np.asarray(pos, dtype=float))
        for name, pos in ch_pos.items()
    }

    selected = {}
    missing = []
    for channel in channel_list:
        match = lookup.get(channel.casefold())
        if match is None:
            missing.append(channel)
            continue
        matched_name, position = match
        selected[matched_name] = position

    if not selected:
        raise ValueError("No requested channels were found in the selected montage.")

    subset = mne.channels.make_dig_montage(
        ch_pos=selected,
        nasion=positions.get("nasion"),
        lpa=positions.get("lpa"),
        rpa=positions.get("rpa"),
        coord_frame=positions.get("coord_frame"),
    )
    return subset, missing


def build_info(montage: mne.channels.DigMontage) -> mne.Info:
    channel_names = list(montage.get_positions()["ch_pos"].keys())
    info = mne.create_info(ch_names=channel_names, sfreq=256.0, ch_types="eeg")
    info.set_montage(montage, on_missing="ignore")
    return info


def build_summary_lines(layout_name: str, info: mne.Info, missing_channels: list[str]) -> list[str]:
    return [
        f"layout={layout_name}",
        f"channels_found={len(info.ch_names)}",
        "channels=" + ",".join(info.ch_names),
        "missing_channels=" + ",".join(missing_channels) if missing_channels else "missing_channels=",
        "exported_figures=yes",
    ]


def export_2d_figure(
    info: mne.Info,
    title: str,
    output_path: Path,
    sphere: str | tuple[float, ...] | None,
) -> None:
    fig = mne.viz.plot_sensors(
        info,
        kind="topomap",
        show_names=True,
        show=False,
        sphere=sphere,
    )
    fig.set_size_inches(10, 8)
    fig.suptitle(title)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def export_3d_figure(
    info: mne.Info,
    title: str,
    output_path: Path,
    sphere: str | tuple[float, ...] | None,
) -> None:
    fig = mne.viz.plot_sensors(
        info,
        kind="3d",
        show_names=True,
        show=False,
        sphere=sphere,
    )
    fig.set_size_inches(10, 8)
    if fig.axes:
        fig.axes[0].set_title(title)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def export_layout(
    output_dir: Path,
    layout_name: str,
    channel_list: list[str] | None,
    sphere: str | tuple[float, ...] | None,
) -> None:
    montage = load_montage(layout_name)
    export_montage, missing_channels = subset_montage(montage, channel_list)
    info = build_info(export_montage)
    title_suffix = f" ({len(info.ch_names)} channels)"
    if missing_channels:
        title_suffix += f" | missing: {len(missing_channels)}"

    export_2d_figure(
        info=info,
        title=f"{layout_name} 2D{title_suffix}",
        output_path=output_dir / f"{layout_name}_2d.png",
        sphere=sphere,
    )
    export_3d_figure(
        info=info,
        title=f"{layout_name} 3D{title_suffix}",
        output_path=output_dir / f"{layout_name}_3d.png",
        sphere=sphere,
    )

    summary_path = output_dir / f"{layout_name}_summary.txt"
    summary_path.write_text(
        "\n".join(build_summary_lines(layout_name, info, missing_channels)) + "\n",
        encoding="utf-8",
    )


def export_case(case_name: str) -> Path:
    case_config = EXPORT_CASES[case_name]
    output_dir = REPO_ROOT / case_config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    for layout_name in resolve_case_layouts(case_config):
        export_layout(
            output_dir=output_dir,
            layout_name=layout_name,
            channel_list=case_config["channel_list"],
            sphere=case_config.get("sphere"),
        )

    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export EEG channel layout figures for the configured montage cases."
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        choices=sorted(EXPORT_CASES),
        default=list(EXPORT_CASES),
        help="One or more export cases defined in config/eeg_config.py.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for case_name in args.cases:
        output_dir = export_case(case_name)
        print(f"Exported case '{case_name}' to: {output_dir}")
    print(f"Default montage: {DEFAULT_MONTAGE}")


if __name__ == "__main__":
    main()
