<h1>WMP</h1>

Code for the paper: 
### World Model-based Perception for Visual Legged Locomotion
[Hang Lai](https://apex.sjtu.edu.cn/members/laihang@apexlab.org), [Jiahang Cao](https://apex.sjtu.edu.cn/members/jhcao@apexlab.org), [JiaFeng Xu](https://scholar.google.com/citations?user=GPmUxtIAAAAJ&hl=zh-CN&oi=ao), [Hongtao Wu](https://scholar.google.com/citations?user=7u0TYgIAAAAJ&hl=zh-CN&oi=ao), [Yunfeng Lin](https://apex.sjtu.edu.cn/members/yflin@apexlab.org), [Tao Kong](https://www.taokong.org/), [Yong Yu](https://scholar.google.com.hk/citations?user=-84M1m0AAAAJ&hl=zh-CN&oi=ao), [Weinan Zhang](https://wnzhang.net/) 

### [🌐 Project Website](https://wmp-loco.github.io/) | [📄 Paper](https://arxiv.org/abs/2409.16784)
   
## Requirements
1. Create a new python virtual env with python 3.6, 3.7 or 3.8 (3.8 recommended)
2. Install pytorch:
    - `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117`
3. Install Isaac Gym
    - Download and install Isaac Gym Preview 3 (Preview 2 will not work!) from https://developer.nvidia.com/isaac-gym
    - `cd isaacgym/python && pip install -e .`
4. Install other packages:
    - `sudo apt-get install build-essential --fix-missing`
    - `sudo apt-get install ninja-build`
    - `pip install setuptools==59.5.0`
    - `pip install ruamel_yaml==0.17.4`
    - `sudo apt install libgl1-mesa-glx -y`
    - `pip install opencv-contrib-python`
    - `pip install -r requirements.txt`

## Training
```
python legged_gym/scripts/train.py --task=a1_amp --headless --sim_device=cuda:0
```
Training takes about 23G GPU memory, and at least 10k iterations recommended.

GO2 (`lyd_dev`): `--task=go2_amp`. AutoDL 环境要点见 [docs/autodl_setup.md](docs/autodl_setup.md)。

GO2 MuJoCo-aligned camera/dynamics finetune is documented in
[docs/go2_mujoco_finetune.md](docs/go2_mujoco_finetune.md).

## Visualization
**Please make sure you have trained the WMP before**
```
python legged_gym/scripts/play.py --task=a1_amp --sim_device=cuda:0 --terrain=climb
```

### GO2 Xbox playback / GO2 手柄测试

`play_xbox.py` keeps the normal WMP/Isaac Gym inference path and replaces only
the velocity command with `/dev/input/js0`. It has no pygame/evdev dependency.
The default Linux Xbox mapping is left stick for forward/lateral velocity and
right-stick X for yaw. Hold `RB` to send stick commands; releasing it sends an
exact zero command, and `Back` exits. Defaults match deployment testing:
forward `0.6 m/s`, lateral `0.0 m/s`, yaw `1.0 rad/s`, deadzone `0.08`.

`play_xbox.py` 保留原来的 WMP/Isaac Gym 推理、深度相机和 RSSM 路径，只将
速度指令替换为 `/dev/input/js0`。按住 `RB` 才输出摇杆指令；松开后严格输出
零指令，适合检查静止时对侧腿跳动是否也在 Isaac Gym 中出现；按 `Back` 退出。

```bash
# 0-5 ms DR run, checkpoint 4000
python legged_gym/scripts/play_xbox.py \
  --task=go2_amp_mujoco_dr_lat0_5 \
  --sim_device=cuda:0 \
  --terrain=climb \
  --load_run=Sep08_16-45-31_WMP_mujoco_dr_lat0_5_ft \
  --checkpoint=4000

# 2-20 ms DR run, checkpoint 3000
python legged_gym/scripts/play_xbox.py \
  --task=go2_amp_mujoco_dr_lat2_20 \
  --sim_device=cuda:0 \
  --terrain=climb \
  --load_run=Sep08_20-54-13_WMP_mujoco_dr_lat2_20_ft \
  --checkpoint=3000
```

Use `--max_forward`, `--max_lateral`, `--max_yaw`, `--deadzone`, and
`--xbox_device` to override the defaults. `--no_deadman` is available for a
simulation-only test but is not recommended. The script defaults to one robot
and runs until the viewer closes or Back is pressed; use `--play_duration 60`
for a bounded run. A 1 Hz `xbox_status` line reports the exact command, measured
base yaw rate and four foot contacts; set `--status_hz 0` to disable it.


## Acknowledgments

We thank the authors of the following projects for making their code open source:

- [leggedgym](https://github.com/leggedrobotics/legged_gym)
- [dreamerv3-torch](https://github.com/NM512/dreamerv3-torch)
- [AMP_for_hardware](https://github.com/Alescontrela/AMP_for_hardware)
- [parkour](https://github.com/ZiwenZhuang/parkour/tree/main)
- [extreme-parkour](https://github.com/chengxuxin/extreme-parkour)



## Citation

If you find this project helpful, please consider citing our paper:
```
@article{lai2024world,
  title={World Model-based Perception for Visual Legged Locomotion},
  author={Lai, Hang and Cao, Jiahang and Xu, Jiafeng and Wu, Hongtao and Lin, Yunfeng and Kong, Tao and Yu, Yong and Zhang, Weinan},
  journal={arXiv preprint arXiv:2409.16784},
  year={2024}
}
```
