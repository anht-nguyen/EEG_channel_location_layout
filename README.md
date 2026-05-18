# EEG Channel Location Layout

This repo exports reference figures for a fixed 32-channel EEG montage derived from the `EEG_CHANNELS` list used in `FloAim6TrialAnalysis`.

The current channel list lives in [config/eeg_config.py](/c:/DATA/git/EEG_channel_location_layout/config/eeg_config.py) and includes:

`Cz, Fz, Fp1, F7, F3, FC1, C3, FC5, FT9, T7, CP5, CP1, P3, P7, PO9, O1, Pz, Oz, O2, PO10, P8, P4, CP2, CP6, T8, FT10, FC6, C4, FC2, F4, F8, Fp2`

## Contents

- [scripts/export_eeg_channel_layouts.py](/c:/DATA/git/EEG_channel_location_layout/scripts/export_eeg_channel_layouts.py): main export script
- [config/eeg_config.py](/c:/DATA/git/EEG_channel_location_layout/config/eeg_config.py): channel list and default montage reference
- [utility/standard_1005.elc](/c:/DATA/git/EEG_channel_location_layout/utility/standard_1005.elc): custom ELC montage source
- [utility/Standard-10-20-Cap32.ced](/c:/DATA/git/EEG_channel_location_layout/utility/Standard-10-20-Cap32.ced): custom Cap32 CED montage source
- [output/channel_layouts](/c:/DATA/git/EEG_channel_location_layout/output/channel_layouts): exported figures and per-layout summaries

## Supported Layouts

The exporter currently supports four layout sources:

- `easycap-M1`
- `standard_1020`
- `standard_1005_elc`
- `cap32_ced`

For built-in layouts, the script uses MNE standard montages. For local assets, it reads:

- `.elc` via `mne.channels.read_custom_montage(...)`
- `.ced` via a small parser in the script that converts the tab-delimited coordinates into an MNE `DigMontage`

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Usage

Export all supported layouts into the default output folder:

```powershell
python scripts/export_eeg_channel_layouts.py
```

Export only selected layouts:

```powershell
python scripts/export_eeg_channel_layouts.py --layouts easycap-M1 cap32_ced
```

Export to a custom directory:

```powershell
python scripts/export_eeg_channel_layouts.py --output-dir output\custom_layouts
```

## Outputs

For each layout, the script writes:

- `*_2d.png`: 2D top-view sensor layout
- `*_3d.png`: 3D sensor layout
- `*_summary.txt`: resolved channel names and any missing channels

Example output files:

- [easycap-M1_2d.png](/c:/DATA/git/EEG_channel_location_layout/output/channel_layouts/easycap-M1_2d.png)
- [easycap-M1_3d.png](/c:/DATA/git/EEG_channel_location_layout/output/channel_layouts/easycap-M1_3d.png)
- [easycap-M1_summary.txt](/c:/DATA/git/EEG_channel_location_layout/output/channel_layouts/easycap-M1_summary.txt)

## Notes

- The script forces MNE and Matplotlib config/cache paths into the repo so it can run in restricted environments without writing to the user profile.
- The default montage reference from the source project is `easycap-M1`, but the exporter is intentionally able to render several alternative layouts for the same `EEG_CHANNELS` list.
