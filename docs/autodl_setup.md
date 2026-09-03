# AutoDL 环境与 GO2 训练要点

本文记录在 AutoDL（Ubuntu 22.04 + RTX 4090）上跑通 `go2_amp` 的关键配置。官方 README 针对 A1 / Isaac Gym Preview 3；本仓库 GO2 配置在 `lyd_dev`。

## 1. 代码

```bash
git clone git@github.com:lu-yidan/WMP.git
cd WMP
git checkout lyd_dev
```

`master` 只有 `a1` / `a1_amp`。GO2 任务、URDF、mocap 都在 `lyd_dev`。

需要 SSH 拉仓库：把机器上的 `~/.ssh/id_ed25519.pub` 加到 GitHub。HTTPS 也可克隆公开仓库。

## 2. Conda 环境

Python **3.8**（Isaac Gym 只支持 3.6–3.8）。

```bash
conda create -n wmp python=3.8 -y
conda activate wmp
```

关键包（已在本机验证）：

| 包 | 版本 | 说明 |
|---|---|---|
| torch / torchvision / torchaudio | 2.4.1+cu121 / 0.19.1+cu121 / 2.4.1 | 与驱动 CUDA 12.x 兼容；不要用 NumPy 1.24 |
| numpy | **1.22.3** | 1.24 会删掉 `np.float`，Isaac Gym 直接报错 |
| setuptools | 59.5.0 | Isaac Gym 安装需要 |
| ruamel.yaml | 0.17.4 | |
| isaacgym | Preview 4 (`1.0rc4`) | Preview 3 已下架，Preview 4 可替代 |

```bash
pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
pip install setuptools==59.5.0 ruamel.yaml==0.17.4
pip install -e /path/to/IsaacGym_Preview_4_Package/isaacgym/python
pip install opencv-contrib-python
pip install -r requirements.txt
pip install numpy==1.22.3 setuptools==59.5.0   # requirements 可能改掉这两个
```

系统包：

```bash
sudo apt-get install -y build-essential ninja-build libgl1-mesa-glx libvulkan1 vulkan-tools libegl1 libgl1
```

Isaac Gym 必须 **先于 torch 导入**。`gymtorch` 第一次会 JIT 编译，属正常。

## 3. Vulkan（没有就会段错误）

`go2_amp` 开了深度相机，`--headless` 仍会创建 graphics device。缺 NVIDIA Vulkan ICD 时，日志停在：

```
GPU Pipeline: enabled
Segmentation fault (core dumped)
```

写入 ICD：

```bash
sudo mkdir -p /usr/share/vulkan/icd.d /usr/share/glvnd/egl_vendor.d
sudo tee /usr/share/vulkan/icd.d/nvidia_icd.json >/dev/null <<'EOF'
{
    "file_format_version": "1.0.0",
    "ICD": {
        "library_path": "libGLX_nvidia.so.0",
        "api_version": "1.3.277"
    }
}
EOF
sudo tee /usr/share/glvnd/egl_vendor.d/10_nvidia.json >/dev/null <<'EOF'
{
    "file_format_version": "1.0.0",
    "ICD": {
        "library_path": "libEGL_nvidia.so.0"
    }
}
EOF
```

每次训练前：

```bash
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
```

建议写进 conda 激活脚本，避免漏设：

```bash
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
echo 'export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}' > $CONDA_PREFIX/etc/conda/activate.d/isaacgym_ld.sh
echo 'export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json' > $CONDA_PREFIX/etc/conda/activate.d/vulkan.sh
```

`libpython3.8.so.1.0` 找不到时，同样是 `LD_LIBRARY_PATH` 没指到 `$CONDA_PREFIX/lib`。

## 4. 启动训练

长期任务用 tmux，SSH 断开也不停：

```bash
tmux new -s wmp
conda activate wmp
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
cd ~/workplace/WMP
python legged_gym/scripts/train.py --task=go2_amp --headless --sim_device=cuda:0
```

- 查看：`tmux attach -t wmp`
- 离开：`Ctrl-b d`（不要 `Ctrl-c`）
- 单卡约 **19–23 GB** 显存，一张 4090 够用

不要用 README 里的 `--task=a1_amp`。

## 5. GO2 训练在跑什么

配置见 `legged_gym/envs/go2/go2_amp_config.py`。

- **4096 个并行环境**，同一个仿真、同一套策略，一起训练
- 其中 **1024** 个环境开深度相机（`depth.camera_num_envs`）
- 地形是一张 **10×20** 的 curriculum 网格：行是难度（0–9），列是地形种类
- 机器人按列分配到不同地形，**不是**每种地形单独训一个策略
- 开局 `max_init_terrain_level = 0`，全部从最容易一档开始，走远了再升难度

地形比例 `terrain_proportions`（按列分配，合计 1.0）：

| 地形 | 比例 | 约多少环境（4096） |
|---|---:|---:|
| wave 波浪 | 0% | 0 |
| rough slope 粗糙斜坡 | 5% | ~205 |
| stairs up 上楼梯 | 15% | ~614 |
| stairs down 下楼梯 | 15% | ~614 |
| discrete 离散障碍 | 0% | 0 |
| gap 间隙 | 25% | ~1024 |
| pit 深坑 / climb | 25% | ~1024 |
| tilt 窄道 | 5% | ~205 |
| crawl 钻洞 | 5% | ~205 |
| rough_flat 粗糙平地 | 5% | ~205 |

当前日志里 `Mean episode terrain_level: 0.0` 表示还在难度 0，还没升 curriculum。
