from __future__ import annotations

from pathlib import Path


DEFAULT_MONTAGE = "easycap-M1"

EEG_32_CHANNELS = [
    "Cz", "Fz",    "Fp1",    "F7",    "F3",    "FC1",    "C3",    "FC5",    "FT9",    "T7",    "CP5",    "CP1",    "P3",    "P7",    "PO9",    "O1",    "Pz",    "Oz",    "O2",    "PO10",    "P8",    "P4",    "CP2",    "CP6",    "T8",    "FT10",    "FC6",    "C4",    "FC2",    "F4",    "F8",    "Fp2",
]

EEG_64_CHANNELS = [
    "Fp1",
    "Fpz",
    "Fp2",
    "AF7",
    "AF3",
    "AFz",
    "AF4",
    "AF8",
    "F7",
    "F5",
    "F3",
    "F1",
    "Fz",
    "F2",
    "F4",
    "F6",
    "F8",
    "FT7",
    "FC5",
    "FC3",
    "FC1",
    "FCz",
    "FC2",
    "FC4",
    "FC6",
    "FT8",
    "T9",
    "T7",
    "C5",
    "C3",
    "C1",
    "Cz",
    "C2",
    "C4",
    "C6",
    "T8",
    "T10",
    "TP7",
    "CP5",
    "CP3",
    "CP1",
    "CPz",
    "CP2",
    "CP4",
    "CP6",
    "TP8",
    "P7",
    "P5",
    "P3",
    "P1",
    "Pz",
    "P2",
    "P4",
    "P6",
    "P8",
    "PO7",
    "PO3",
    "POz",
    "PO4",
    "PO8",
    "O1",
    "Oz",
    "O2",
    "Iz",
]

EEG_22_channels_UET175 = [
    "Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz"
    ]

EXPORT_CASES = {
    "all_mne_montages": {
        "description": "Plot all built-in MNE montages using each montage's native channels.",
        "channel_list": None,
        "montage": "all_builtin",
        "sphere": None,
        "output_dir": Path("output") / "all_MNE_montages",
    },
    "eeg_32_channels": {
        "description": "Plot the configured 32-channel EEG list (default EMOTIV Epoc FLEX configuration) on the default easycap montage.",
        "channel_list": EEG_32_CHANNELS,
        "montage": DEFAULT_MONTAGE,
        "sphere": "eeglab",
        "output_dir": Path("output") / "eeg_32_channels",
    },
    "uet175_22_channels": {
        "description": "Plot the configured 22-channel EEG list (Epoc FLEX configuration in UET175 dataset) on the default easycap montage.",
        "channel_list": EEG_22_channels_UET175,
        "montage": DEFAULT_MONTAGE,
        "sphere": "eeglab",
        "output_dir": Path("output") / "uet175_22_channels",
    },
    "bci2000_64_channels": {
        "description": "Plot the configured 64-channel EEG list (BCI2000 configuration) on 10-10 system.",
        "channel_list": EEG_64_CHANNELS,
        "montage": ['standard_1005', 'easycap-M1'],
        "sphere": "eeglab",
        "output_dir": Path("output") / "bci2000_64_channels",
    },
}
