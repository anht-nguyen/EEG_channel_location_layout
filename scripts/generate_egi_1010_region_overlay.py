from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_SVG = REPO_ROOT / "output" / "manuscript_figure_2" / "high_density_128_channel.svg"
DEFAULT_BACKGROUND_PNG = REPO_ROOT / "utility" / "egi_montage.png"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "egi_1010_equivalent_regions"
DEFAULT_DPI = 300
DEFAULT_FORMATS = ["png", "svg", "pdf"]

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

BASE_MARKER_STYLE = {
    "facecolor": "#5A8FCB",
    "edgecolor": "#184F8F",
    "linewidth": 2.0,
    "size": 72,
}

HEAD_STYLE = {
    "color": "#111111",
    "linewidth": 1.8,
}

REGION_STYLES = {
    "adjacent_pair": {
        "fill": "#68C3F0",
        "edge": "#2B90C5",
        "template_alpha": 0.23,
        "template_padding": 22.0,
        "background_alpha": 0.20,
        "background_padding": 18.0,
        "marker_size": 78,
    },
    "c_pair": {
        "fill": "#F4A261",
        "edge": "#D97706",
        "template_alpha": 0.24,
        "template_padding": 20.0,
        "background_alpha": 0.19,
        "background_padding": 16.0,
        "marker_size": 78,
    },
}

BACKGROUND_PNG_REGION_POSITIONS = {
    "E13": np.array([298.0, 277.0], dtype=float),
    "E29": np.array([266.0, 314.0], dtype=float),
    "E30": np.array([295.0, 343.0], dtype=float),
    "E35": np.array([219.0, 321.0], dtype=float),
    "E36": np.array([251.0, 361.0], dtype=float),
    "E37": np.array([293.0, 392.0], dtype=float),
    "E41": np.array([212.0, 367.0], dtype=float),
    "E42": np.array([259.0, 405.0], dtype=float),
    "E87": np.array([429.0, 393.0], dtype=float),
    "E93": np.array([464.0, 406.0], dtype=float),
    "E103": np.array([511.0, 369.0], dtype=float),
    "E104": np.array([471.0, 362.0], dtype=float),
    "E105": np.array([429.0, 343.0], dtype=float),
    "E110": np.array([505.0, 323.0], dtype=float),
    "E111": np.array([459.0, 315.0], dtype=float),
    "E112": np.array([427.0, 279.0], dtype=float),
}

REGION_SPECS = [
    {
        "label": "E35 / E29 / E13 and mirrored E112 / E111 / E110",
        "style_key": "adjacent_pair",
        "regions": [
            {"channels": ["E35", "E29", "E13"]},
            {"channels": ["E112", "E111", "E110"]},
        ],
    },
    {
        "label": "C3 / C4-equivalent regions",
        "style_key": "c_pair",
        "regions": [
            {
                "channels": ["E41", "E36", "E30", "E42", "E37"],
                "annotation": {"text": "C3", "position": "centroid"},
            },
            {
                "channels": ["E105", "E104", "E103", "E87", "E93"],
                "annotation": {"text": "C4", "position": "centroid"},
            },
        ],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay transparent 10-10-equivalent EGI HydroCel-128 regions on the stored 2D layout."
    )
    parser.add_argument(
        "--template-svg",
        type=Path,
        default=DEFAULT_TEMPLATE_SVG,
        help=f"HydroCel-128 SVG template to parse. Default: {DEFAULT_TEMPLATE_SVG}",
    )
    parser.add_argument(
        "--background-png",
        type=Path,
        default=DEFAULT_BACKGROUND_PNG,
        help=(
            "Optional background montage PNG. When provided, draw the transparent regions directly on that image "
            f"instead of reconstructing the clean SVG layout. Recommended value: {DEFAULT_BACKGROUND_PNG}"
        ),
    )
    parser.add_argument(
        "--render-mode",
        choices=["background_png", "template_svg"],
        default="background_png",
        help="Default render path. Use 'background_png' to draw on the montage image or 'template_svg' for the clean reconstructed layout.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for exported figures. Default: {DEFAULT_OUTPUT_DIR}",
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
    parser.add_argument(
        "--show-legend",
        action="store_true",
        help="Show a legend on the output. By default the legend is shown for the clean template and hidden for background PNG mode.",
    )
    return parser.parse_args()


def parse_svg_template(svg_path: Path) -> tuple[tuple[float, float], dict[str, np.ndarray], list[np.ndarray]]:
    if not svg_path.exists():
        raise FileNotFoundError(f"Template SVG not found: {svg_path}")

    root = ET.parse(svg_path).getroot()
    view_box = [float(value) for value in root.attrib["viewBox"].split()]
    _, _, width, height = view_box

    uses = root.findall('.//svg:g[@id="PathCollection_1"]/svg:use', SVG_NS)
    if len(uses) != 128:
        raise ValueError(f"Expected 128 channel markers in {svg_path}, found {len(uses)}.")

    channel_positions = {
        f"E{index}": np.array([float(use.attrib["x"]), float(use.attrib["y"])], dtype=float)
        for index, use in enumerate(uses, start=1)
    }

    head_paths: list[np.ndarray] = []
    for group in root.findall(".//svg:g", SVG_NS):
        group_id = group.attrib.get("id", "")
        if not group_id.startswith("line2d_"):
            continue
        path = group.find("svg:path", SVG_NS)
        if path is None:
            continue
        head_paths.append(parse_svg_path_points(path.attrib["d"]))

    if not head_paths:
        raise ValueError(f"No head-outline paths found in {svg_path}.")

    return (width, height), channel_positions, head_paths


def parse_svg_path_points(path_data: str) -> np.ndarray:
    numbers = [float(value) for value in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", path_data)]
    if len(numbers) % 2 != 0:
        raise ValueError("SVG path coordinate list has an odd number of values.")
    return np.array(list(zip(numbers[0::2], numbers[1::2])), dtype=float)


def convex_hull(points: np.ndarray) -> np.ndarray:
    unique_points = sorted({(float(x), float(y)) for x, y in points})
    if len(unique_points) <= 1:
        return np.array(unique_points, dtype=float)

    def cross(origin: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in unique_points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[float, float]] = []
    for point in reversed(unique_points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return np.array(lower[:-1] + upper[:-1], dtype=float)


def expand_polygon(points: np.ndarray, padding: float) -> np.ndarray:
    hull = convex_hull(points)
    if len(hull) == 0:
        raise ValueError("Cannot expand an empty polygon.")
    if len(hull) == 1:
        return hull.copy()

    centroid = hull.mean(axis=0)
    expanded_points = []
    for point in hull:
        direction = point - centroid
        norm = np.linalg.norm(direction)
        if norm == 0.0:
            expanded_points.append(point.copy())
            continue
        expanded_points.append(point + padding * direction / norm)
    return np.array(expanded_points, dtype=float)


def draw_base_layout(
    ax: plt.Axes,
    head_paths: list[np.ndarray],
    channel_positions: dict[str, np.ndarray],
) -> None:
    for path_points in head_paths:
        ax.plot(path_points[:, 0], path_points[:, 1], zorder=1, **HEAD_STYLE)

    all_points = np.array(list(channel_positions.values()))
    ax.scatter(
        all_points[:, 0],
        all_points[:, 1],
        s=BASE_MARKER_STYLE["size"],
        c=BASE_MARKER_STYLE["facecolor"],
        edgecolors=BASE_MARKER_STYLE["edgecolor"],
        linewidths=BASE_MARKER_STYLE["linewidth"],
        zorder=2,
    )


def draw_region_overlays(ax: plt.Axes, channel_positions: dict[str, np.ndarray]) -> list[Line2D]:
    return draw_region_overlays_with_mode(
        ax,
        channel_positions,
        render_mode="template",
    )


def draw_region_overlays_with_mode(
    ax: plt.Axes,
    channel_positions: dict[str, np.ndarray],
    *,
    render_mode: str,
) -> list[Line2D]:
    legend_handles: list[Line2D] = []
    is_background_mode = render_mode == "background_png"

    for region_group in REGION_SPECS:
        style = REGION_STYLES[region_group["style_key"]]
        alpha = style["background_alpha"] if is_background_mode else style["template_alpha"]
        padding = style["background_padding"] if is_background_mode else style["template_padding"]

        for region in region_group["regions"]:
            points = np.array([channel_positions[channel] for channel in region["channels"]], dtype=float)
            overlay_shape = expand_polygon(points, padding)
            ax.add_patch(
                Polygon(
                    overlay_shape,
                    closed=True,
                    facecolor=style["fill"],
                    edgecolor=style["edge"],
                    linewidth=2.2,
                    alpha=alpha,
                    joinstyle="round",
                    zorder=1.5,
                )
            )

            if not is_background_mode:
                ax.scatter(
                    points[:, 0],
                    points[:, 1],
                    s=style["marker_size"],
                    c=style["fill"],
                    edgecolors="#333333",
                    linewidths=1.4,
                    zorder=3,
                )

            annotation = region.get("annotation")
            if annotation is not None and not is_background_mode:
                if annotation.get("position") == "centroid":
                    anchor = points.mean(axis=0)
                else:
                    anchor = channel_positions[annotation["anchor"]]
                ax.text(
                    anchor[0] + annotation.get("dx", 0.0),
                    anchor[1] + annotation.get("dy", 0.0),
                    annotation["text"],
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    color="#333333",
                    bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none", "pad": 1.8},
                    zorder=4,
                )

        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                markerfacecolor=style["fill"],
                markeredgecolor=style["edge"],
                markeredgewidth=1.6,
                markersize=8,
                label=region_group["label"],
            )
        )

    return legend_handles


def configure_axes(ax: plt.Axes, canvas_size: tuple[float, float]) -> None:
    width, height = canvas_size
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_aspect("equal")
    ax.axis("off")


def save_outputs(
    fig: plt.Figure,
    output_dir: Path,
    *,
    source_path: Path,
    output_stem: str,
    summary_lines: list[str],
    dpi: int,
    formats: list[str],
    tight: bool,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    exported_paths: list[Path] = []

    for file_format in formats:
        output_path = output_dir / f"{output_stem}.{file_format}"
        save_kwargs = {"pad_inches": 0.0 if not tight else 0.05}
        if tight:
            save_kwargs["bbox_inches"] = "tight"
        if file_format == "png":
            save_kwargs["dpi"] = dpi
        fig.savefig(output_path, **save_kwargs)
        exported_paths.append(output_path)

    summary_path = output_dir / f"{output_stem}_summary.txt"
    summary_lines = [f"source_path={source_path}", *summary_lines]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    exported_paths.append(summary_path)
    return exported_paths


def build_template_figure(template_svg: Path, *, show_legend: bool) -> plt.Figure:
    canvas_size, channel_positions, head_paths = parse_svg_template(template_svg)
    width, height = canvas_size
    fig, ax = plt.subplots(figsize=(width / 90.0, height / 90.0))
    configure_axes(ax, canvas_size)
    draw_base_layout(ax, head_paths, channel_positions)
    legend_handles = draw_region_overlays_with_mode(ax, channel_positions, render_mode="template")
    if show_legend:
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.02),
            ncol=1,
            frameon=False,
            fontsize=9,
        )
    return fig


def build_background_figure(background_png: Path, *, show_legend: bool) -> plt.Figure:
    if not background_png.exists():
        raise FileNotFoundError(f"Background PNG not found: {background_png}")

    image = mpimg.imread(background_png)
    height, width = image.shape[:2]
    fig = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(image, extent=(0, width, height, 0))
    configure_axes(ax, (float(width), float(height)))
    legend_handles = draw_region_overlays_with_mode(
        ax,
        BACKGROUND_PNG_REGION_POSITIONS,
        render_mode="background_png",
    )
    if show_legend:
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.01),
            ncol=1,
            frameon=True,
            facecolor="white",
            edgecolor="none",
            fontsize=9,
        )
    return fig


def main() -> None:
    args = parse_args()
    if args.render_mode == "template_svg":
        show_legend = True
        figure = build_template_figure(args.template_svg, show_legend=show_legend)
        exported_paths = save_outputs(
            figure,
            args.output_dir,
            source_path=args.template_svg,
            output_stem="egi_1010_equivalent_regions",
            summary_lines=[
                "render_mode=template_svg",
                "base_montage=GSN-HydroCel-128",
                "region_pair_1=E35,E29,E13 | E112,E111,E110",
                "region_pair_2=E41,E36(C3),E30,E42,E37 | E105,E104(C4),E103,E87,E93",
            ],
            dpi=args.dpi,
            formats=args.formats,
            tight=True,
        )
    else:
        background_png = args.background_png
        show_legend = args.show_legend
        figure = build_background_figure(background_png, show_legend=show_legend)
        exported_paths = save_outputs(
            figure,
            args.output_dir,
            source_path=background_png,
            output_stem="layout_egi_montage_1010_equivalent_regions",
            summary_lines=[
                "render_mode=background_png",
                "background_reference=utility/egi_montage.png",
                "base_montage=GSN-HydroCel-128 (rendered on provided montage image)",
                "region_pair_1=E35,E29,E13 | E112,E111,E110",
                "region_pair_2=E41,E36(C3),E30,E42,E37 | E105,E104(C4),E103,E87,E93",
            ],
            dpi=args.dpi,
            formats=args.formats,
            tight=False,
        )
    plt.close(figure)

    for path in exported_paths:
        print(path)


if __name__ == "__main__":
    main()
