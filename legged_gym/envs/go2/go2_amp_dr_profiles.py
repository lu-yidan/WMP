"""MuJoCo-aligned finetune profiles with go2-matched domain randomization."""

from .go2_amp_config import GO2AMPCfg


class GO2AMPMujocoDRLat0_5Cfg(GO2AMPCfg):
    """Downward camera + go2 DR + action latency [0, 5] ms."""

    class depth(GO2AMPCfg.depth):
        y_angle = [15, 25]

    class domain_rand(GO2AMPCfg.domain_rand):
        # Restore source go2_amp DR ranges (flags stay on for critic dims).
        friction_range = [0.5, 2.0]
        restitution_range = [0.0, 0.0]
        added_mass_range = [0.0, 3.0]
        link_mass_range = [0.8, 1.2]
        com_x_pos_range = [-0.05, 0.05]
        com_y_pos_range = [-0.05, 0.05]
        com_z_pos_range = [-0.05, 0.05]
        push_robots = True
        stiffness_multiplier_range = [0.8, 1.2]
        damping_multiplier_range = [0.8, 1.2]
        motor_strength_range = [0.8, 1.2]
        latency_range = [0.00, 0.005]


class GO2AMPMujocoDRLat2_20Cfg(GO2AMPCfg):
    """Downward camera + go2 DR + action latency [2, 20] ms.

    With sim dt=5 ms this discretizes to 1-4 control substeps (5-20 ms).
    """

    class depth(GO2AMPCfg.depth):
        y_angle = [15, 25]

    class domain_rand(GO2AMPCfg.domain_rand):
        friction_range = [0.5, 2.0]
        restitution_range = [0.0, 0.0]
        added_mass_range = [0.0, 3.0]
        link_mass_range = [0.8, 1.2]
        com_x_pos_range = [-0.05, 0.05]
        com_y_pos_range = [-0.05, 0.05]
        com_z_pos_range = [-0.05, 0.05]
        push_robots = True
        stiffness_multiplier_range = [0.8, 1.2]
        damping_multiplier_range = [0.8, 1.2]
        motor_strength_range = [0.8, 1.2]
        latency_range = [0.002, 0.020]
