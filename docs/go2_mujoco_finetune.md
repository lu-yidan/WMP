# GO2 AMP MuJoCo-aligned finetune / MuJoCo 对齐微调

This branch is a checkpoint-compatible finetune profile for `go2_amp`. It does not change policy/world-model tensor shapes.

本分支用于在不改变策略及 world-model 张量形状的前提下，对现有 `go2_amp` checkpoint 做 MuJoCo 契约微调。

## Contract changes / 契约变化

| Parameter | Finetune value | MuJoCo source |
| --- | ---: | --- |
| camera position | `[0.33, 0, 0.10]` m | `go2.xml` `wmp_depth` |
| camera pitch | explicit profile: legacy `-5–5°` or downward `15–25°` | controlled A/B comparison; MuJoCo nominal `20°` |
| image/FOV/range | `64×64`, square `58°`, `0–2 m` | deployment depth contract |
| joint passive damping | `0.1` | `go2.xml` joint default |
| joint armature | `0.01` | `go2.xml` joint default |
| joint friction | `0.2` | MuJoCo `frictionloss` approximation |
| hip/thigh effort | `23.7 Nm` | URDF and MuJoCo |
| calf effort | `45.43 Nm` | MuJoCo motor range |
| collision cylinders | retained as cylinders | MuJoCo collision model |
| self collision | enabled | MuJoCo non-parent collision behavior |
| contact friction | fixed `1.0` | validation scenes |

Domain-randomization flags remain enabled because their privileged values are part of the resumed critic observation. Their ranges are collapsed to the nominal MuJoCo values, preserving dimensions while removing parameter variation. Pushes are disabled. PD control remains `Kp=40`, `Kd=1`, action scale `0.25`, simulation step `5 ms`, policy rate `50 Hz`, depth/world rate `10 Hz`.

Isaac Gym's URDF importer did not retain `AssetOptions.armature` in actor DOF properties during validation, so the profile also writes `dof_armature=0.01` explicitly in the DOF-property callback. A 16-environment runtime readback verifies the effective value.

为保持旧 checkpoint 的 critic observation 维度，domain randomization 的开关仍为开启状态，但范围全部收缩到 MuJoCo 名义值；外力 push 已关闭。PD 控制仍为 `Kp=40`、`Kd=1`，action scale 为 `0.25`，物理步长 `5 ms`，策略频率 `50 Hz`，深度/world-model 频率 `10 Hz`。

## Server resume / 服务器续训

```bash
cd ~/workspace/WMP
git fetch origin
git switch finetune/go2_amp_mujoco_dynamics
git pull --ff-only

conda activate wmp
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

# Both profiles resume exactly the same source:
# logs/go2_amp_example/WMP/model_20000.pt
WMP_PYTHON="$CONDA_PREFIX/bin/python" \
WMP_NUM_ENVS=4096 \
WMP_FINETUNE_ITERATIONS=5000 \
WMP_CAMERA_PROFILE=legacy \
./scripts/train_go2_amp_mujoco_finetune.sh
```

The first controlled run should use `legacy`: it preserves the source
checkpoint's `-5–5°` camera distribution and changes only the robot
model/dynamics side of the experiment. For this reason, `legacy` is also the
launcher default when `WMP_CAMERA_PROFILE` is omitted. Train the `down` profile
only after evaluating this checkpoint in Isaac Gym and MuJoCo.

第一阶段先使用 `legacy`：它保留源 checkpoint 的 `-5–5°` 相机分布，
只验证机器人模型与动力学修改。因此，不设置 `WMP_CAMERA_PROFILE` 时
启动器也默认选择 `legacy`。完成 Isaac Gym 和 MuJoCo 对比后，
再单独训练 `down` 版本。

For a controlled camera ablation, keep checkpoint, seed and all other settings
identical and change only the profile. Use separate GPUs or run them sequentially;
two 4096-environment jobs should not share one GPU.

```bash
# A: source-camera distribution, isolates the dynamics/model change
WMP_CAMERA_PROFILE=legacy WMP_SEED=1 \
  ./scripts/train_go2_amp_mujoco_finetune.sh

# B: D435/MuJoCo camera distribution, same source and seed
WMP_CAMERA_PROFILE=down WMP_SEED=1 \
  ./scripts/train_go2_amp_mujoco_finetune.sh
```

The registered tasks are `go2_amp_mujoco_cam_legacy` (`-5–5°`) and
`go2_amp_mujoco_cam_down` (`15–25°`). Their timestamped output directories end
in `WMP_mujoco_cam_m5_p5_ft` and `WMP_mujoco_camdown15_25_ft`, respectively, so
checkpoints never overwrite each other. This also avoids relying on an edited
base `go2_amp` configuration.

为了做严格的相机消融实验，两组实验应使用相同源 checkpoint、相同 seed、
相同动力学和相同训练轮数，只切换 `WMP_CAMERA_PROFILE`。两个 4096 环境任务
不要同时挤在同一张 GPU 上；应使用不同 GPU，或顺序执行。

`WMP_FINETUNE_ITERATIONS` means additional iterations after the checkpoint's internal `iter`. The supplied local `model_20000.pt` is named 20000 but stores `iter=0`; the launcher resumes weights and optimizers correctly, but new checkpoint numbering follows that internal metadata.

`WMP_FINETUNE_ITERATIONS` 表示在 checkpoint 内部 `iter` 之后额外训练的轮数。本地 `model_20000.pt` 虽然文件名为 20000，但内部保存的是 `iter=0`；权重和 PPO optimizer 仍会恢复，新 checkpoint 的编号则按内部元数据继续。

The downward-profile output directory matches
`logs/go2_amp_example/<timestamp>_WMP_mujoco_camdown15_25_ft` by default.
Override source/output without editing code:

```bash
WMP_SOURCE_RUN=WMP \
WMP_SOURCE_CHECKPOINT=20000 \
WMP_RUN_NAME=WMP_mujoco_camdown15_25_ft_v2 \
WMP_FINETUNE_ITERATIONS=3000 \
./scripts/train_go2_amp_mujoco_finetune.sh
```

This first profile aligns the high-impact passive/contact settings. It enables
self collision and penalizes any `thigh` or `calf` body whose net contact force
exceeds 0.1 N; the reward scale is `-1.0` before the standard policy-step `dt`
scaling. This signal does not distinguish robot self-contact from terrain
contact on those bodies.

The collision shapes are still not identical. The Isaac training URDF uses a
0.11 m-long thigh collision box, while the official MuJoCo model uses 0.213 m;
the URDF also contains a third distal `calflower1` cylinder that is absent from
the MuJoCo collision model. Distal calf/foot inertial aggregation and
PhysX-vs-MuJoCo contact solver semantics remain different. Treat these as a
separate, versioned collision-model experiment rather than silently
compensating with action scale.

这一版启用了自碰撞，并对净接触力超过 0.1 N 的 `thigh`/`calf`
刚体计入碰撞惩罚；但该信号无法区分自碰撞和腿部碰到地形。Isaac
训练 URDF 的大腿碰撞盒长 0.11 m，MuJoCo 为 0.213 m；URDF 还多一段
`calflower1` 末端圆柱。因此碰撞体、小腿/脚掌惯量聚合及两种求解器
仍未完全对齐；后续应作为独立模型版本验证，不要用 action scale 暗中补偿。
