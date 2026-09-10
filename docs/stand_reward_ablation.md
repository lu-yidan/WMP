# Stand reward ablation / 站立奖励对照（2026-09-09）

新增 task `go2_amp_mujoco_dr_lat0_5_stand`，launcher profile
`down_dr_lat0_5_stand`。复用 lat2-20 stand 的完全相同奖励：pose=1、quiet=0.25、
contact=0.5；保留 lat0-5 的相机 [15,25]、动力学、DR 与延迟 [0,5] ms。
没有改变现有 task、奖励实现或 resume 行为。源 checkpoint 选 3000，与此前
两组导出保持一致，而不是自动挑选最新的 4000。

## First paired experiment / 第一组成对实验

在服务器的 WMP 仓库与 wmp conda 环境中，确认 GPU 空闲后执行：

```bash
WMP_SOURCE_RUN=Sep08_16-45-31_WMP_mujoco_dr_lat0_5_ft \
WMP_SOURCE_CHECKPOINT=3000 \
WMP_CAMERA_PROFILE=down_dr_lat0_5_stand \
WMP_RUN_NAME=WMP_lat0_5_stand_ablation_s1 \
WMP_FINETUNE_ITERATIONS=1000 WMP_NUM_ENVS=4096 \
WMP_SEED=1 WMP_SIM_DEVICE=cuda:0 \
./scripts/train_go2_amp_mujoco_finetune.sh
```

原奖励继续训练对照：相同命令只改 profile 为 `down_dr_lat0_5`，run name 为
`WMP_lat0_5_continue_ablation_s1`。不要从新 stand 模型续训作为对照。
不要将两项任务放到同一张显存不足的 GPU 上；这里没有自动启动服务器训练。

对 2–20 ms 也做同样的一对：source 改为
`Sep08_20-54-13_WMP_mujoco_dr_lat2_20_ft`，profile 分别为
`down_dr_lat2_20` / `down_dr_lat2_20_stand`，独立 run name。
各组先追加 1000 updates，比较同等追加次数；有明确趋势后用 seeds 1/2/3
复验。两个 latency 源模型训练历史不同，这不是严格的仅延迟因果实验；
严格隔离延迟需要从同一个父 checkpoint 训练各组。

## Diagnosis / 排查顺序

1. 固定 checkpoint、指令、地形等级、相机和 RSSM 采样设置，多次评估原模型。
   Isaac 使用 `--terrain_level 8`；零命令站立与 0.6 m/s 越障分开测，
   不要在靠近障碍时松开 RB。记录完整实际指令，不能只看摇杆位置。
2. 比较原奖励继续训练 vs stand。若两者都退化，先查 resume/训练分布；
   若只有 stand 退化，再做奖励消融，而非同时修改相机、延迟和动作尺度。
3. 下一轮可以仅把 contact 从 0.5 降到 0.1，其他不变（尚未实现此变体）。
   另外单独检查 `<0.1` 的站立门控、零命令覆盖率，避免和奖励权重一起改。

记录：零指令时 |yaw rate|、关节速度、四足接触率；climb/gap 各至少 10 次
通过/起跳/落地成功数及失败类型。先固定简单地形再测第 8 级。
总 reward 不适合直接跨奖励配方排名；训练 episode 的成功率也不替代固定评估。

当前 resume 恢复 actor/critic、world-model 和 PPO optimizer；AMP discriminator
与 AMP normalizer 的恢复被注释，WM optimizer 默认不恢复。
所以继续训练对照是必要的，不能把 checkpoint 前后的所有差异归因于 stand。
本次不改变这些行为。文件名 update 数和内部 iter 分开记录；旧模型 iter 常为 0。

当前 contact 奖励的 last_contacts 在 feet_air_time 中已被更新，一帧过滤实现
值得独立修正；先保持本次两组奖励一致。没有证据认定 reward clipping 是主因。

## Server launch record / 服务器启动记录

更新：用户随后取消原奖励继续训练对照。已向 PID 693002/693003 发送
SIGINT；nohup 后台任务未响应，随后以 SIGTERM 停止。GPU0/1 不再安排任务，
保留日志与已产生的 checkpoint。
本轮以 Sep08 两组 model_3000.pt 为原奖励基线，只运行 GPU2/3 站立版。
下面表格为历史启动记录，不代表四组仍在运行。

2026-09-09，SSH alias `gpu4090`，仓库 `/root/workplace/WMP`，代码 `ff0de09`。
按用户要求向旧进程 5232（go2_amp）和 98921（a1_amp）发送 SIGINT；
保留磁盘上的 `go2_amp_example/WMP/model_31000.pt` 和
`a1_amp_example/WMP/model_25000.pt`，未保证保存中断前最后一个 update。

| GPU | PID at launch | Run name | Additional updates |
| --- | --- | --- | --- |
| 0 | 693002 | WMP_lat0_5_continue_ablation_s1 | 1000 |
| 1 | 693003 | WMP_lat2_20_continue_ablation_s1 | 1000 |
| 2 | 671778 (existing, untouched) | WMP_mujoco_dr_lat2_20_stand_ft | 2000 |
| 3 | 692669 | WMP_lat0_5_stand_ablation_s1 | 1000 |

新任务均使用 4096 envs、seed=1、各自 Sep08 run 的 model_3000.pt；
sim/rl/wm device 显式指定同一张卡。使用 nohup，SSH 断开不终止训练。
日志在 `logs/finetune_launch/`：
`lat0_5_continue_ablation_s1_cuda0.log`、`lat2_20_continue_ablation_s1_cuda1.log`、
`lat0_5_stand_ablation_s1_cuda3.log`。
GPU2 既有日志为 `dr_lat2_20_stand_cuda2_v2.log`，与 GPU1 对比时选双方
checkpoint 1000，而非把 GPU2 的 2000 与 GPU1 的 1000 混比。
PID 仅用于这次启动记录，后续操作前需重新核对进程身份。

## Approved reward ablations / 确认执行的奖励消融

用户确认将释放的 GPU0/1 改为以下任务，替代已取消的原奖励续训：

| GPU | Profile (`WMP_CAMERA_PROFILE`) | pose / quiet / contact |
| --- | --- | --- |
| 0 | down_dr_lat0_5_stand_no_contact | 1 / 0.25 / 0 |
| 1 | down_dr_lat0_5_stand_quiet | 0 / 0.25 / 0 |
| 3 (unchanged) | down_dr_lat0_5_stand | 1 / 0.25 / 0.5 |

两项均从 `Sep08_16-45-31_WMP_mujoco_dr_lat0_5_ft/model_3000.pt` 开始，
4096 envs、seed=1、追加 1000 updates；sim/rl/wm 分别全部在所在 GPU。
run names: `WMP_lat0_5_stand_no_contact_ablation_s1` / `WMP_lat0_5_stand_quiet_ablation_s1`。
日志：`logs/finetune_launch/lat0_5_stand_no_contact_ablation_s1_cuda0.log` /
`logs/finetune_launch/lat0_5_stand_quiet_ablation_s1_cuda1.log`。
任务名为 profile 去掉 `down_` 后加 `go2_amp_mujoco_` 前缀（见 task registry）。
配置对比验证：相对完整 stand 仅上述 reward scales 改变；既有全局奖励
（例如 dof_error）并未删除，quiet-only 指仅新增站立奖励中的 quiet。
门控、AMP、相机、延迟与 resume 行为不变。GPU2 的 2–20 ms 站立版保持运行。

启动代码版本 `f7b8874`，GPU0 PID=695117，GPU1 PID=695118。
实际输出目录（均在 `logs/go2_amp_example/`）：
`Sep09_22-33-14_WMP_lat0_5_stand_no_contact_ablation_s1`、
`Sep09_22-33-12_WMP_lat0_5_stand_quiet_ablation_s1`。
完整奖励对照目录为 `Sep09_22-25-47_WMP_lat0_5_stand_ablation_s1`。

## Lat2-20 quiet follow-up / 20 ms quiet 后续实验（2026-09-10）

**启动前用户改为 [0,20] ms。以下 lat2-20 命令仅为原计划，未启动。**
实际使用 profile `down_dr_lat0_20_stand_quiet`，task
`go2_amp_mujoco_dr_lat0_20_stand_quiet`，run name
`WMP_lat0_20_stand_quiet_ablation_s1`。仍从下面指定的 Sep08 lat2-20
model_3000 续训，GPU0、4096 envs、seed1、追加1000轮。
实际延迟取值 0/5/10/15/20 ms；因此与源模型相比同时改变 quiet 奖励和
延迟下限，不是纯奖励消融。日志为
`logs/finetune_launch/lat0_20_stand_quiet_ablation_s1_cuda0.log`。
实际启动代码 `2df4d2e`，GPU0 PID=18585，输出目录
`logs/go2_amp_example/Sep10_15-25-01_WMP_lat0_20_stand_quiet_ablation_s1`。
已确认加载指定 checkpoint 并完成第 0 轮训练，无启动 OOM/异常。
用户随后将目标提高到 5000 updates。原 PID18585 仅完成约 3 轮，已 SIGTERM
停止并保留原日志/初始 checkpoint；从同一 Sep08 model_3000 重新开始，不从
model_0 续训，以保留一致的初始化路径。新 run name 为
`WMP_lat0_20_stand_quiet_5000_s1`，日志为
`logs/finetune_launch/lat0_20_stand_quiet_5000_s1_cuda0.log`。
环境数4096、seed1、GPU0、[0,20]ms、quiet=0.25 均不变。

用户反馈 lat0-5 quiet 在 MuJoCo 表现不错，追加 lat2-20 quiet 对照。
这里“20 ms”沿用既有随机延迟 [2,20] ms，不是固定 20 ms；sim dt=5 ms
时实际离散为 5/10/15/20 ms。仅新增 stand_quiet=0.25，stand_pose/contact=0，
原有全局奖励保留。相机仍为向下 [15,25] 度，resume 行为不变。

```bash
WMP_SOURCE_RUN=Sep08_20-54-13_WMP_mujoco_dr_lat2_20_ft \
WMP_SOURCE_CHECKPOINT=3000 \
WMP_CAMERA_PROFILE=down_dr_lat2_20_stand_quiet \
WMP_RUN_NAME=WMP_lat2_20_stand_quiet_ablation_s1 \
WMP_FINETUNE_ITERATIONS=1000 WMP_NUM_ENVS=4096 \
WMP_SEED=1 WMP_SIM_DEVICE=cuda:0 \
./scripts/train_go2_amp_mujoco_finetune.sh
```

在 gpu4090 的 `/root/workplace/WMP` 启动前确认 GPU0 空闲。
日志 `logs/finetune_launch/lat2_20_stand_quiet_ablation_s1_cuda0.log`。
play 使用 task `go2_amp_mujoco_dr_lat2_20_stand_quiet`，与 lat0-5 quiet
统一比较追加 1000 updates、相同地形等级/速度/采样设置。
