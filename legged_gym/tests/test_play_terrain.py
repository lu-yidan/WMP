"""Test origin selection without initializing Isaac Gym or a GPU."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

import numpy as np
import torch


class PlaybackTerrainTest(unittest.TestCase):
    def origins(self, count, level=None):
        source = Path(__file__).parents[1] / "envs/base/legged_robot.py"
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LeggedRobot")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "_get_env_origins")
        namespace = {"torch": torch, "np": np}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
        cfg = NS(mesh_type="trimesh", max_init_terrain_level=5,
                 curriculum=False, num_rows=10, num_cols=1)
        if level is not None:
            cfg.playback_level = level
        env = NS(cfg=NS(terrain=cfg), num_envs=count, device="cpu",
                 terrain=NS(env_origins=np.arange(30).reshape(10, 1, 3)))
        namespace["_get_env_origins"](env)
        return env

    def test_single_robot_fixed_level(self):
        env = self.origins(1, 8)
        self.assertEqual(env.terrain_levels.tolist(), [8])
        self.assertEqual(env.env_origins.tolist(), [[24., 25., 26.]])

    def test_multi_robot_fixed_level(self):
        self.assertEqual(self.origins(10, 4).terrain_levels.tolist(), [4] * 10)

    def test_original_assignment_unchanged(self):
        self.assertEqual(self.origins(10).terrain_levels.tolist(), list(range(10)))
        self.assertEqual(self.origins(1).terrain_levels.tolist(), [0])


if __name__ == "__main__":
    unittest.main()
