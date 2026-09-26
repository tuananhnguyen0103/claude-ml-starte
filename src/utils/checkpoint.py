"""Lưu / tìm / khôi phục checkpoint. Thiết kế để phiên Colab/Kaggle bị ngắt bất kỳ lúc nào vẫn resume được."""
import glob
import os
import random

import numpy as np
import torch


def save_ckpt(ckpt_dir, state, keep_last=2):
    os.makedirs(ckpt_dir, exist_ok=True)
    final = os.path.join(ckpt_dir, f"step_{state['step']:08d}.pt")
    tmp = final + ".tmp"
    torch.save(state, tmp)
    os.replace(tmp, final)            # ghi nguyên tử: bị ngắt giữa chừng cũng không hỏng ckpt cũ
    for old in sorted(glob.glob(os.path.join(ckpt_dir, "step_*.pt")))[:-keep_last]:
        os.remove(old)
    return final


def latest_ckpt(ckpt_dir):
    ckpts = sorted(glob.glob(os.path.join(ckpt_dir, "step_*.pt")))
    return ckpts[-1] if ckpts else None


def load_ckpt(path):
    # weights_only=False vì state chứa optimizer + RNG. Chỉ load file do chính mình tạo.
    return torch.load(path, map_location="cpu", weights_only=False)


def rng_state():
    return {"py": random.getstate(), "np": np.random.get_state(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}


def set_rng_state(s):
    random.setstate(s["py"])
    np.random.set_state(s["np"])
    torch.set_rng_state(s["torch"])
    if s["cuda"] is not None and torch.cuda.is_available() and len(s["cuda"]) == torch.cuda.device_count():
        torch.cuda.set_rng_state_all(s["cuda"])
