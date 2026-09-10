#!/usr/bin/env bash
set -euo pipefail

# Resume a contract-compatible GO2 WMP checkpoint using the MuJoCo-aligned
# branch configuration. max_iterations is the number of *additional* updates.
WMP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WMP_PYTHON="${WMP_PYTHON:-python}"
SOURCE_RUN="${WMP_SOURCE_RUN:-WMP}"
SOURCE_CHECKPOINT="${WMP_SOURCE_CHECKPOINT:-20000}"
# Keep the source checkpoint's camera distribution by default so the first
# experiment isolates the MuJoCo-aligned robot model/dynamics changes.
CAMERA_PROFILE="${WMP_CAMERA_PROFILE:-legacy}"
NUM_ENVS="${WMP_NUM_ENVS:-4096}"
ITERATIONS="${WMP_FINETUNE_ITERATIONS:-5000}"
SIM_DEVICE="${WMP_SIM_DEVICE:-cuda:2}"
SEED="${WMP_SEED:-1}"
CHECKPOINT_PATH="${WMP_ROOT}/logs/go2_amp_example/${SOURCE_RUN}/model_${SOURCE_CHECKPOINT}.pt"

case "${CAMERA_PROFILE}" in
  down)
    TASK="go2_amp_mujoco_cam_down"
    DEFAULT_RUN_NAME="WMP_mujoco_camdown15_25_ft"
    ;;
  legacy)
    TASK="go2_amp_mujoco_cam_legacy"
    DEFAULT_RUN_NAME="WMP_mujoco_cam_m5_p5_ft"
    ;;
  down_dr_lat0_5)
    # Downward camera + go2-matched DR + latency [0, 5] ms
    TASK="go2_amp_mujoco_dr_lat0_5"
    DEFAULT_RUN_NAME="WMP_mujoco_dr_lat0_5_ft"
    ;;
  down_dr_lat2_20)
    # Downward camera + go2-matched DR + latency [2, 20] ms
    TASK="go2_amp_mujoco_dr_lat2_20"
    DEFAULT_RUN_NAME="WMP_mujoco_dr_lat2_20_ft"
    ;;
  down_dr_lat0_5_stand)
    TASK="go2_amp_mujoco_dr_lat0_5_stand"
    DEFAULT_RUN_NAME="WMP_mujoco_dr_lat0_5_stand_ft"
    ;;
  down_dr_lat0_5_stand_no_contact)
    TASK="go2_amp_mujoco_dr_lat0_5_stand_no_contact"
    DEFAULT_RUN_NAME="WMP_lat0_5_stand_no_contact_ablation_s1"
    ;;
  down_dr_lat0_5_stand_quiet)
    TASK="go2_amp_mujoco_dr_lat0_5_stand_quiet"
    DEFAULT_RUN_NAME="WMP_lat0_5_stand_quiet_ablation_s1"
    ;;
  down_dr_lat2_20_stand_quiet)
    TASK="go2_amp_mujoco_dr_lat2_20_stand_quiet"
    DEFAULT_RUN_NAME="WMP_lat2_20_stand_quiet_ablation_s1"
    ;;
  down_dr_lat2_20_stand)
    # Same lat2-20 profile with zero-command stance rewards only.
    TASK="go2_amp_mujoco_dr_lat2_20_stand"
    DEFAULT_RUN_NAME="WMP_mujoco_dr_lat2_20_stand_ft"
    ;;
  *)
    echo "Unknown WMP_CAMERA_PROFILE=${CAMERA_PROFILE}; expected legacy, down, down_dr_lat0_5, down_dr_lat2_20, down_dr_lat0_5_stand, down_dr_lat0_5_stand_no_contact, down_dr_lat0_5_stand_quiet, down_dr_lat2_20_stand_quiet, or down_dr_lat2_20_stand." >&2
    exit 2
    ;;
esac
RUN_NAME="${WMP_RUN_NAME:-${DEFAULT_RUN_NAME}}"

if [[ ! -f "${CHECKPOINT_PATH}" ]]; then
  echo "Missing resume checkpoint: ${CHECKPOINT_PATH}" >&2
  echo "Set WMP_SOURCE_RUN and WMP_SOURCE_CHECKPOINT, or sync the checkpoint first." >&2
  exit 2
fi

if ! PYTHON_BIN="$(command -v "${WMP_PYTHON}")"; then
  echo "Python executable not found: ${WMP_PYTHON}" >&2
  exit 2
fi
PYTHON_PREFIX="$(cd "$(dirname "${PYTHON_BIN}")/.." && pwd)"
export LD_LIBRARY_PATH="${PYTHON_PREFIX}/lib:${LD_LIBRARY_PATH:-}"
if [[ -z "${VK_ICD_FILENAMES:-}" && -f /usr/share/vulkan/icd.d/nvidia_icd.json ]]; then
  export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
fi
cd "${WMP_ROOT}"
echo "Resume: ${CHECKPOINT_PATH}"
echo "Experiment: profile=${CAMERA_PROFILE} task=${TASK} run=${RUN_NAME} seed=${SEED}"
exec "${PYTHON_BIN}" legged_gym/scripts/train.py \
  --task="${TASK}" \
  --headless \
  --sim_device="${SIM_DEVICE}" \
  --rl_device="${SIM_DEVICE}" \
  --wm_device="${SIM_DEVICE}" \
  --num_envs="${NUM_ENVS}" \
  --resume \
  --load_run="${SOURCE_RUN}" \
  --checkpoint="${SOURCE_CHECKPOINT}" \
  --run_name="${RUN_NAME}" \
  --seed="${SEED}" \
  --max_iterations="${ITERATIONS}"
