# EEG Channel Location Layout

This repo exports EEG sensor-layout figures from config-defined cases in [config/eeg_config.py](/c:/DATA/git/EEG_channel_location_layout/config/eeg_config.py).

The main script is [scripts/export_eeg_channel_layouts.py](/c:/DATA/git/EEG_channel_location_layout/scripts/export_eeg_channel_layouts.py). It reads `EXPORT_CASES` from the config, resolves one or more montages for each case, keeps the native montage geometry for plotting, optionally limits the visible channels to a configured subset, and exports:

- `*_2d.png`
- `*_3d.png`
- `*_summary.txt`

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Current runtime dependencies are listed in [requirements.txt](/c:/DATA/git/EEG_channel_location_layout/requirements.txt):

- `mne`
- `matplotlib`
- `numpy`
- `eeg_positions`

## Montage Sources

The exporter supports three montage-source patterns:

- MNE built-in montages via `mne.channels.make_standard_montage(...)`
- all built-in MNE montages via `"montage": "all_builtin"`
- `eeg_positions` for `standard_1020`, `standard_1010`, and `standard_1005`

`eeg_positions` is used to replace MNE's `standard_10**` montages:

- `standard_1020` -> `eeg_positions.get_elec_coords(system="1020", as_mne_montage=True)`
- `standard_1010` -> `eeg_positions.get_elec_coords(system="1010", as_mne_montage=True)`
- `standard_1005` -> `eeg_positions.get_elec_coords(system="1005", as_mne_montage=True)`

## Config Model

Each case in `EXPORT_CASES` defines:

- `channel_list`
- `montage`
- `sphere`
- `output_dir`

Supported `montage` forms are:

- one montage name string, for example `"easycap-M1"`
- `"all_builtin"`
- a list of montage names, for example `["standard_1005", "easycap-M1"]`

`channel_list=None` means export the montage's full native channel set. If `channel_list` is provided, the script matches channel names case-insensitively against the native montage, keeps the full native montage in `plot_sensors()`, and shows only the requested subset on the final figure.

`sphere` is passed through to `mne.viz.plot_sensors(...)` for both 2D and 3D exports. Example values in the current config include `None` and `"eeglab"`.

This matters for subset cases such as `uet175_22_channels`: `sphere="eeglab"` needs landmarks like `Fpz`, `Oz`, `T7`, and `T8` to remain present in the plotting `Info`, even if only a smaller channel subset is shown on the figure.

## Current Cases

The current config defines these cases:

- `all_mne_montages`: export every built-in MNE montage with native channels to [output/all_MNE_montages](/c:/DATA/git/EEG_channel_location_layout/output/all_MNE_montages)
- `eeg_32_channels`: export the 32-channel Emotiv-style list on `easycap-M1` to [output/eeg_32_channels](/c:/DATA/git/EEG_channel_location_layout/output/eeg_32_channels)
- `uet175_22_channels`: export the 22-channel UET175 list on `easycap-M1` to [output/uet175_22_channels](/c:/DATA/git/EEG_channel_location_layout/output/uet175_22_channels)
- `bci2000_64_channels`: export the 64-channel BCI2000 list on both `standard_1005` and `easycap-M1` to [output/bci2000_64_channels](/c:/DATA/git/EEG_channel_location_layout/output/bci2000_64_channels)

The configured channel lists currently include:

- `EEG_32_CHANNELS`
- `EEG_22_channels_UET175`
- `EEG_64_CHANNELS`

## Usage

Run all configured cases:

```powershell
python scripts/export_eeg_channel_layouts.py
```

Run one or more selected cases:

```powershell
python scripts/export_eeg_channel_layouts.py --cases eeg_32_channels
python scripts/export_eeg_channel_layouts.py --cases bci2000_64_channels uet175_22_channels
```

Example with the full interpreter path:

```powershell
& "C:\Program Files\Python310\python.exe" c:/DATA/git/EEG_channel_location_layout/scripts/export_eeg_channel_layouts.py --cases bci2000_64_channels
```

## Outputs

For each resolved montage inside a case, the script writes:

- `*_2d.png`: 2D sensor layout
- `*_3d.png`: 3D sensor layout with a fixed diagonal camera view
- `*_summary.txt`: exported channels and any missing requested channels

Examples:

- [output/eeg_32_channels/easycap-M1_2d.png](/c:/DATA/git/EEG_channel_location_layout/output/eeg_32_channels/easycap-M1_2d.png)
- [output/eeg_32_channels/easycap-M1_3d.png](/c:/DATA/git/EEG_channel_location_layout/output/eeg_32_channels/easycap-M1_3d.png)
- [output/eeg_32_channels/easycap-M1_summary.txt](/c:/DATA/git/EEG_channel_location_layout/output/eeg_32_channels/easycap-M1_summary.txt)
- [output/bci2000_64_channels/standard_1005_2d.png](/c:/DATA/git/EEG_channel_location_layout/output/bci2000_64_channels/standard_1005_2d.png)
- [output/bci2000_64_channels/easycap-M1_2d.png](/c:/DATA/git/EEG_channel_location_layout/output/bci2000_64_channels/easycap-M1_2d.png)

## Notes

- The script forces MNE and Matplotlib config/cache paths into the repo so it can run without writing to the user profile.
- For subset exports, the figure uses the native montage for geometry and sphere fitting, but only the requested channels are labeled and shown.
- Missing configured channels are reported in the summary file.
- For `standard_10**` systems, the layout comes from `eeg_positions`, not MNE.
