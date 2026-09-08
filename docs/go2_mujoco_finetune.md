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

There are two experiment families:

1. **Camera ablation** (`legacy` / `down`): domain-randomization flags stay on for critic observation compatibility, but ranges collapse to MuJoCo nominal values and pushes are disabled. Isolates camera pitch while freezing dynamics DR.
2. **DR + latency** (`down_dr_lat0_5` / `down_dr_lat2_20`): keeps the downward camera (`15–25°`) and restores the source `go2_amp` DR ranges (friction, mass, CoM, Kp/Kd, motor strength, pushes), then varies only action latency.

PD nominal control remains `Kp=40`, `Kd=1`, action scale `0.25`, simulation step `5 ms`, policy rate `50 Hz`, depth/world rate `10 Hz`.

Isaac Gym's URDF importer did not retain `AssetOptions.armature` in actor DOF properties during validation, so the profile also writes `dof_armature=0.01` explicitly in the DOF-property callback. A 16-environment runtime readback verifies the effective value.

本分支有两类实验：（1）相机消融 `legacy`/`down`：DR 开关保留但范围塌到 MuJoCo 名义值，push 关闭；（2）DR+延迟 `down_dr_lat0_5`/`down_dr_lat2_20`：固定向下相机，恢复与源 go2 一致的 DR，只改 action latency。名义 PD 仍为 `Kp=40`、`Kd=1`。

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

The registered camera-ablation tasks are `go2_amp_mujoco_cam_legacy` (`-5–5°`) and
`go2_amp_mujoco_cam_down` (`15–25°`). Their timestamped output directories end
in `WMP_mujoco_cam_m5_p5_ft` and `WMP_mujoco_camdown15_25_ft`, respectively, so
checkpoints never overwrite each other. This also avoids relying on an edited
base `go2_amp` configuration.

为了做严格的相机消融实验，两组实验应使用相同源 checkpoint、相同 seed、
相同动力学和相同训练轮数，只切换 `WMP_CAMERA_PROFILE`。两个 4096 环境任务
不要同时挤在同一张 GPU 上；应使用不同 GPU，或顺序执行。

## Domain-rand + latency finetune / DR 与延迟微调

After the downward camera looked better in the collapsed-DR ablation, restore the
source go2 DR and compare action-latency ranges. Both profiles use camera
`15–25°` and the same DR table as the original `go2_amp` training snapshot:

| Parameter | Range |
| --- | ---: |
| friction | `[0.5, 2.0]` |
| added base mass | `[0, 3]` kg |
| link mass scale | `[0.8, 1.2]` |
| CoM xyz | `±0.05` m |
| Kp / Kd multipliers | `[0.8, 1.2]` |
| motor strength | `[0.8, 1.2]` |
| pushes | enabled (`max_push_vel_xy=1.0`) |

| `WMP_CAMERA_PROFILE` | Task | Latency config | Discrete steps @ `dt=5 ms` | Run suffix |
| --- | --- | ---: | ---: | --- |
| `down_dr_lat0_5` | `go2_amp_mujoco_dr_lat0_5` | `[0, 5]` ms | `0–1` (0 / 5 ms) | `WMP_mujoco_dr_lat0_5_ft` |
| `down_dr_lat2_20` | `go2_amp_mujoco_dr_lat2_20` | `[2, 20]` ms | `1–4` (5 / 10 / 15 / 20 ms) | `WMP_mujoco_dr_lat2_20_ft` |

Latency is applied inside the PD decimation loop by reusing `last_actions` for
the first N sim substeps. Lower bounds use `ceil`, so `[2, 20] ms` does not
collapse to a zero-delay sample under a 5 ms physics step.

```bash
# Match original go2 latency
WMP_SIM_DEVICE=cuda:2 WMP_CAMERA_PROFILE=down_dr_lat0_5 WMP_SEED=1 \
  ./scripts/train_go2_amp_mujoco_finetune.sh

# Longer latency stress test
WMP_SIM_DEVICE=cuda:3 WMP_CAMERA_PROFILE=down_dr_lat2_20 WMP_SEED=1 \
  ./scripts/train_go2_amp_mujoco_finetune.sh
```

Always set `WMP_SIM_DEVICE` to a free GPU. The launcher also passes matching
`--rl_device` / `--wm_device`; otherwise the world model can default to
`cuda:0` and OOM against an existing job.

在塌缩 DR 的相机消融中，向下相机效果更好。随后恢复源 go2 的 DR，并只对比
action latency：`[0,5] ms` 与 `[2,20] ms`。延迟在 PD decimation 内用
`last_actions` 实现；下界按 `ceil` 换算，因此在 `dt=5 ms` 下 `[2,20] ms`
会落在 1–4 个 substep（5–20 ms），不会抽到 0 延迟。启动时务必指定空闲
`WMP_SIM_DEVICE`，否则 world model 可能占到 `cuda:0`。

`WMP_FINETUNE_ITERATIONS` means additional iterations after the checkpoint's internal `iter`. The supplied local `model_20000.pt` is named 20000 but stores `iter=0`; the launcher resumes weights and optimizers correctly, but new checkpoint numbering follows that internal metadata.

`WMP_FINETUNE_ITERATIONS` 表示在 checkpoint 内部 `iter` 之后额外训练的轮数。本地 `model_20000.pt` 虽然文件名为 20000，但内部保存的是 `iter=0`；权重和 PPO optimizer 仍会恢复，新 checkpoint 的编号则按内部元数据继续。

Override source/output without editing code:

```bash
WMP_SOURCE_RUN=WMP \
WMP_SOURCE_CHECKPOINT=20000 \
WMP_RUN_NAME=WMP_mujoco_dr_lat0_5_ft_v2 \
WMP_FINETUNE_ITERATIONS=3000 \
WMP_CAMERA_PROFILE=down_dr_lat0_5 \
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
