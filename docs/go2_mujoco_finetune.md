# GO2 AMP MuJoCo-aligned finetune / MuJoCo 对齐微调

This branch is a checkpoint-compatible finetune profile for `go2_amp`. It does not change policy/world-model tensor shapes.

本分支用于在不改变策略及 world-model 张量形状的前提下，对现有 `go2_amp` checkpoint 做 MuJoCo 契约微调。

## Contract changes / 契约变化

| Parameter | Finetune value | MuJoCo source |
| --- | ---: | --- |
| camera position | `[0.33, 0, 0.10]` m | `go2.xml` `wmp_depth` |
| camera pitch | random downward `15–25°` | MuJoCo nominal `20°` and requested D435 mounting range |
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

# Expected source: logs/go2_amp_example/WMP/model_20000.pt
WMP_PYTHON="$CONDA_PREFIX/bin/python" \
WMP_NUM_ENVS=4096 \
WMP_FINETUNE_ITERATIONS=5000 \
./scripts/train_go2_amp_mujoco_finetune.sh
```

`WMP_FINETUNE_ITERATIONS` means additional iterations after the checkpoint's internal `iter`. The supplied local `model_20000.pt` is named 20000 but stores `iter=0`; the launcher resumes weights and optimizers correctly, but new checkpoint numbering follows that internal metadata.

`WMP_FINETUNE_ITERATIONS` 表示在 checkpoint 内部 `iter` 之后额外训练的轮数。本地 `model_20000.pt` 虽然文件名为 20000，但内部保存的是 `iter=0`；权重和 PPO optimizer 仍会恢复，新 checkpoint 的编号则按内部元数据继续。

The output directory is `logs/go2_amp_example/WMP_mujoco_camdown15_25_ft` by default. Override source/output without editing code:

```bash
WMP_SOURCE_RUN=WMP \
WMP_SOURCE_CHECKPOINT=20000 \
WMP_RUN_NAME=WMP_mujoco_camdown15_25_ft_v2 \
WMP_FINETUNE_ITERATIONS=3000 \
./scripts/train_go2_amp_mujoco_finetune.sh
```

This first profile aligns the high-impact passive/contact settings. Distal calf/foot inertial aggregation and PhysX-vs-MuJoCo contact solver semantics are still not identical; record those as separate model revisions rather than silently compensating with action scale.

这一版先对齐高影响的被动关节和接触参数。小腿/脚掌的惯量聚合以及 PhysX 与 MuJoCo 接触求解器仍不可能完全等价；后续应作为独立模型版本记录，不要通过修改 action scale 暗中补偿。
