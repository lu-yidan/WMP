"""Explicit camera profiles for controlled GO2 AMP finetune experiments."""

from .go2_amp_config import GO2AMPCfg


class GO2AMPCameraLegacyCfg(GO2AMPCfg):
    """Original WMP camera-pitch distribution used by the source checkpoint."""

    class depth(GO2AMPCfg.depth):
        y_angle = [-5, 5]


class GO2AMPCameraDownCfg(GO2AMPCfg):
    """D435/MuJoCo-aligned camera-pitch distribution, positive means down."""

    class depth(GO2AMPCfg.depth):
        y_angle = [15, 25]
