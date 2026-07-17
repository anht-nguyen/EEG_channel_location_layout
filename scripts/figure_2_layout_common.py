from __future__ import annotations

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
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D

from scripts.export_eeg_channel_layouts import (
    _channel_group_indices,
    build_info,
    load_montage,
    subset_montage,
)


DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "manuscript_figure_2"
DEFAULT_FORMATS = ["png", "svg", "pdf"]
DEFAULT_DPI = 300
CONSISTENT_SCALP_VIEW_BOUNDS = {
    "xlim": (-0.131, 0.131),
    "ylim": (-0.131, 0.131),
}

COLORS = {
    "highlight_fill": "#1F6BC1",
    "highlight_edge": "#163E72",
    "context_fill": "#FFFFFF",
    "context_edge": "#AAB6C3",
    "core_fill": "#0A5B68",
    "adjacent_fill": "#2F88B7",
    "occasional_fill": "#E1B44C",
    "outline": "#17324D",
    "text": "#1C2635",
}

NAME_ALIASES = {
    "T3": "T7",
    "T4": "T8",
    "T5": "P7",
    "T6": "P8",
}


def resolve_channel_names(
    available_names: list[str],
    requested_names: list[str] | None,
) -> tuple[list[str], list[str]]:
    if requested_names is None:
        return list(available_names), []

    lookup = {name.casefold(): name for name in available_names}
    resolved_names: list[str] = []
    missing_names: list[str] = []

    for requested_name in requested_names:
        candidates = [requested_name]
        alias = NAME_ALIASES.get(requested_name)
        if alias is not None:
            candidates.append(alias)

        matched_name = None
        for candidate in candidates:
            matched_name = lookup.get(candidate.casefold())
            if matched_name is not None:
                break

        if matched_name is None:
            missing_names.append(requested_name)
            continue
        if matched_name not in resolved_names:
            resolved_names.append(matched_name)

    return resolved_names, missing_names


def build_color_arrays(
    info: mne.Info,
    visible_names: list[str],
    *,
    default_facecolor: str,
    default_edgecolor: str,
    default_markersize: float,
    default_linewidth: float,
    show_context: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    default_face = np.array(to_rgba(default_facecolor), dtype=float)
    default_edge = np.array(to_rgba(default_edgecolor), dtype=float)
    hidden_face = default_face.copy()
    hidden_edge = default_edge.copy()
    hidden_face[-1] = 0.0
    hidden_edge[-1] = 0.0

    facecolors = np.repeat(hidden_face[None, :], len(info.ch_names), axis=0)
    edgecolors = np.repeat(hidden_edge[None, :], len(info.ch_names), axis=0)
    markersizes = np.zeros(len(info.ch_names), dtype=float)
    linewidths = np.zeros(len(info.ch_names), dtype=float)

    visible_set = set(visible_names)
    for index, channel_name in enumerate(info.ch_names):
        if channel_name not in visible_set:
            continue
        facecolors[index] = default_face
        edgecolors[index] = default_edge
        markersizes[index] = default_markersize
        linewidths[index] = default_linewidth

    if show_context:
        hidden_indices = [
            index for index, channel_name in enumerate(info.ch_names) if channel_name not in visible_set
        ]
        for index in hidden_indices:
            markersizes[index] = default_markersize
            linewidths[index] = default_linewidth
        return facecolors, edgecolors, markersizes, linewidths

    hidden_indices = [
        index for index, channel_name in enumerate(info.ch_names) if channel_name not in visible_set
    ]
    if hidden_indices:
        facecolors[hidden_indices, -1] = 0.0
        edgecolors[hidden_indices, -1] = 0.0
    return facecolors, edgecolors, markersizes, linewidths


def apply_group_styles(
    info: mne.Info,
    facecolors: np.ndarray,
    edgecolors: np.ndarray,
    markersizes: np.ndarray,
    linewidths: np.ndarray,
    group_styles: list[dict],
) -> list[dict]:
    applied_groups: list[dict] = []
    for group_style in group_styles:
        resolved_names, missing_names = resolve_channel_names(info.ch_names, group_style["names"])
        if missing_names:
            missing_text = ", ".join(missing_names)
            raise ValueError(f"Missing tier channels: {missing_text}")

        face_rgba = np.array(to_rgba(group_style["facecolor"]), dtype=float)
        edge_rgba = np.array(to_rgba(group_style["edgecolor"]), dtype=float)

        for index, channel_name in enumerate(info.ch_names):
            if channel_name not in resolved_names:
                continue
            facecolors[index] = face_rgba
            edgecolors[index] = edge_rgba
            if "markersize" in group_style:
                markersizes[index] = group_style["markersize"]
            if "linewidth" in group_style:
                linewidths[index] = group_style["linewidth"]

        applied_groups.append(
            {
                "label": group_style["label"],
                "names": resolved_names,
                "facecolor": group_style["facecolor"],
                "edgecolor": group_style["edgecolor"],
                "markersize": group_style.get("markersize", 8),
            }
        )
    return applied_groups


def set_collection_styles(
    fig: plt.Figure,
    info: mne.Info,
    facecolors: np.ndarray,
    edgecolors: np.ndarray,
    markersizes: np.ndarray,
    linewidths: np.ndarray,
) -> None:
    for axis in fig.axes:
        for collection in getattr(axis, "collections", []):
            if not hasattr(collection, "get_facecolors") or not hasattr(collection, "get_edgecolors"):
                continue

            current_facecolors = collection.get_facecolors()
            current_edgecolors = collection.get_edgecolors()

            if len(current_facecolors) == 0 and len(current_edgecolors) == 0:
                continue

            if len(current_facecolors) == 1 and len(info.ch_names) > 1:
                current_facecolors = np.repeat(current_facecolors, len(info.ch_names), axis=0)
            if len(current_edgecolors) == 1 and len(info.ch_names) > 1:
                current_edgecolors = np.repeat(current_edgecolors, len(info.ch_names), axis=0)

            if len(current_facecolors) == len(info.ch_names):
                collection.set_facecolors(facecolors)
            if len(current_edgecolors) == len(info.ch_names):
                collection.set_edgecolors(edgecolors)

            if hasattr(collection, "get_sizes"):
                current_sizes = collection.get_sizes()
                if len(current_sizes) == 1 and len(info.ch_names) > 1:
                    current_sizes = np.repeat(current_sizes, len(info.ch_names), axis=0)
                if len(current_sizes) == len(info.ch_names):
                    collection.set_sizes(markersizes)

            if hasattr(collection, "get_linewidths"):
                current_linewidths = collection.get_linewidths()
                if len(current_linewidths) == 1 and len(info.ch_names) > 1:
                    current_linewidths = np.repeat(current_linewidths, len(info.ch_names), axis=0)
                if len(current_linewidths) == len(info.ch_names):
                    collection.set_linewidths(linewidths)


def configure_figure(fig: plt.Figure, figure_size: tuple[float, float] | None = None) -> None:
    if figure_size is None:
        figure_size = (10, 8)
    fig.set_size_inches(*figure_size)


def apply_fixed_view_bounds(
    fig: plt.Figure,
    fixed_view_bounds: dict[str, tuple[float, float]] | None,
) -> None:
    if fixed_view_bounds is None:
        return

    for axis in fig.axes:
        if hasattr(axis, "set_xlim"):
            axis.set_xlim(*fixed_view_bounds["xlim"])
        if hasattr(axis, "set_ylim"):
            axis.set_ylim(*fixed_view_bounds["ylim"])
        if hasattr(axis, "set_aspect"):
            axis.set_aspect("equal")


def add_titles(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.suptitle(title, fontsize=17, color=COLORS["text"], y=0.985)
    fig.text(0.5, 0.94, subtitle, ha="center", va="top", fontsize=16, color=COLORS["text"])


def style_channel_labels(fig: plt.Figure, label_names: list[str], label_style: dict | None) -> None:
    if label_style is None:
        return

    label_lookup = {label.casefold() for label in label_names}
    for axis in fig.axes:
        for text in axis.texts:
            if text.get_text().casefold() not in label_lookup:
                continue
            if "fontsize" in label_style:
                text.set_fontsize(label_style["fontsize"])
            if "fontweight" in label_style:
                text.set_fontweight(label_style["fontweight"])
            if "color" in label_style:
                text.set_color(label_style["color"])


def add_group_legend(fig: plt.Figure, applied_groups: list[dict], legend_style: dict | None = None) -> None:
    if not fig.axes:
        return
    legend_style = legend_style or {}

    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=group["facecolor"],
            markeredgecolor=group["edgecolor"],
            markeredgewidth=1.4,
            markersize=legend_style.get("markersize", group.get("markersize", 10) ** 0.5),
            label=group["label"],
        )
        for group in applied_groups
    ]
    legend = fig.axes[0].legend(
        handles=legend_handles,
        loc=legend_style.get("loc", "lower right"),
        bbox_to_anchor=legend_style.get("bbox_to_anchor", (1.00, 0.00)),
        ncol=1,
        frameon=False,
        fontsize=legend_style.get("fontsize", 8.5),
        borderaxespad=0.0,
        labelspacing=0.45,
        handletextpad=0.6,
    )
    legend.set_zorder(10)


def build_figure(
    spec_key: str,
    spec: dict,
    *,
    include_titles: bool,
) -> tuple[plt.Figure, list[str], list[str], list[dict]]:
    montage = load_montage(spec["montage"])
    visible_names, missing_channels = subset_montage(montage, spec["channel_list"])
    info = build_info(montage)

    requested_label_names = spec.get("label_names") or []
    label_names, missing_label_names = resolve_channel_names(info.ch_names, requested_label_names)
    if missing_label_names:
        missing_text = ", ".join(missing_label_names)
        raise ValueError(f"{spec_key} is missing label channels: {missing_text}")

    group_indices = _channel_group_indices(info, visible_names)
    fig = mne.viz.plot_sensors(
        info,
        kind="topomap",
        show_names=label_names,
        show=False,
        sphere=spec.get("sphere"),
        ch_groups=[group_indices],
    )

    facecolors, edgecolors, markersizes, linewidths = build_color_arrays(
        info,
        visible_names,
        default_facecolor=spec["visible_style"]["facecolor"],
        default_edgecolor=spec["visible_style"]["edgecolor"],
        default_markersize=spec["visible_style"].get("markersize", 48),
        default_linewidth=spec["visible_style"].get("linewidth", 1.5),
        show_context=spec.get("show_context", False),
    )

    applied_groups: list[dict] = []
    if spec.get("group_styles"):
        applied_groups = apply_group_styles(
            info,
            facecolors,
            edgecolors,
            markersizes,
            linewidths,
            spec["group_styles"],
        )

    set_collection_styles(fig, info, facecolors, edgecolors, markersizes, linewidths)
    configure_figure(fig, spec.get("figure_size"))
    apply_fixed_view_bounds(fig, spec.get("fixed_view_bounds"))
    style_channel_labels(fig, label_names, spec.get("label_style"))
    if include_titles:
        add_titles(fig, spec["title"], spec["subtitle"])
    if applied_groups:
        add_group_legend(fig, applied_groups, spec.get("legend_style"))

    return fig, visible_names, missing_channels, applied_groups


def save_figure(fig: plt.Figure, output_dir: Path, stem: str, formats: list[str], dpi: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    exported_paths: list[Path] = []
    for file_format in formats:
        output_path = output_dir / f"{stem}.{file_format}"
        save_kwargs = {"bbox_inches": "tight"}
        if file_format == "png":
            save_kwargs["dpi"] = dpi
        fig.savefig(output_path, **save_kwargs)
        exported_paths.append(output_path)
    return exported_paths


def save_titleless_png(fig: plt.Figure, output_dir: Path, stem: str, dpi: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"layout_{stem}_titleless.png"
    fig.savefig(output_path, dpi=dpi)
    return output_path


def write_figure_summary(
    output_dir: Path,
    stem: str,
    spec_key: str,
    spec: dict,
    visible_names: list[str],
    missing_channels: list[str],
    applied_groups: list[dict],
) -> Path:
    summary_path = output_dir / f"{stem}_summary.txt"
    summary_lines = [
        f"figure_key={spec_key}",
        f"title={spec['title']}",
        f"subtitle={spec['subtitle']}",
        f"montage_template={spec['montage']}",
        f"channels_shown={len(visible_names)}",
        "visible_channels=" + ",".join(visible_names),
        "missing_channels=" + ",".join(missing_channels) if missing_channels else "missing_channels=",
    ]

    for group in applied_groups:
        summary_lines.append(f"{group['label']}=" + ",".join(group["names"]))

    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return summary_path


def export_spec(
    spec_key: str,
    spec: dict,
    output_dir: Path,
    formats: list[str],
    dpi: int,
) -> tuple[list[Path], Path]:
    figure, visible_names, missing_channels, applied_groups = build_figure(
        spec_key,
        spec,
        include_titles=True,
    )
    stem = spec_key
    exported_paths = save_figure(figure, output_dir, stem, formats, dpi)
    summary_path = write_figure_summary(
        output_dir,
        stem,
        spec_key,
        spec,
        visible_names,
        missing_channels,
        applied_groups,
    )
    plt.close(figure)

    titleless_figure, _, _, _ = build_figure(
        spec_key,
        spec,
        include_titles=False,
    )
    titleless_path = save_titleless_png(titleless_figure, output_dir, stem, dpi)
    plt.close(titleless_figure)
    return exported_paths + [titleless_path], summary_path


def write_manifest(
    output_dir: Path,
    exported_specs: list[tuple[str, list[Path], Path]],
    *,
    manifest_name: str,
) -> Path:
    manifest_path = output_dir / manifest_name
    manifest_lines = []
    for spec_key, figure_paths, summary_path in exported_specs:
        manifest_lines.append(f"figure_key={spec_key}")
        manifest_lines.append("figure_files=" + ",".join(str(path) for path in figure_paths))
        manifest_lines.append(f"summary_file={summary_path}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return manifest_path
