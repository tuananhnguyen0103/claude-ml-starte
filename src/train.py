"""Train CIFAR-10. Chạy được ở local (--smoke, CPU), Colab và Kaggle; tự resume từ checkpoint mới nhất.

Ví dụ:
    python -m src.train --smoke                                    # kiểm tra nhanh trước khi push
    python -m src.train --run-name run-001-baseline                # train thật (Colab/Kaggle)
    python -m src.train --config configs/exp_ls01.yaml --run-name run-002-ls01 --set train.epochs=40
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.config import load_config
from src.data import build_datasets, make_train_loader, make_val_loader
from src.model import build_model
from src.utils.checkpoint import latest_ckpt, load_ckpt, rng_state, save_ckpt, set_rng_state
from src.utils.env import default_path, detect_env
from src.utils.metrics import append_metrics
from src.utils.run_logger import NullLogger, RunLogger


def git_commit():
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], text=True,
                                        stderr=subprocess.DEVNULL).strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default="configs/base.yaml")
    p.add_argument("--run-name", default="dev")
    p.add_argument("--data-dir", default=None, help="mặc định theo môi trường, xem src/utils/env.py")
    p.add_argument("--ckpt-dir", default=None, help="mặc định <thư mục ckpt của môi trường>/<run-name>")
    p.add_argument("--resume", default="auto", help="auto | none | <đường dẫn .pt>")
    p.add_argument("--time-budget-h", type=float, default=11.0, help="tự dừng sạch sau N giờ (đặt nhỏ hơn giới hạn phiên)")
    p.add_argument("--save-every-min", type=float, default=20.0)
    p.add_argument("--max-steps", type=int, default=None, help="dừng sau N step như khi hết time budget (để test resume)")
    p.add_argument("--hub-repo", default=None, help="(tùy chọn) HF Hub repo đồng bộ ckpt, vd user/cifar-ckpt")
    p.add_argument("--log-branch", default=None, help="(tùy chọn) đẩy tiến độ lên branch git này để Claude đọc, vd runs")
    p.add_argument("--log-remote", default=None, help="remote nhận log (mặc định: origin của repo hiện tại)")
    p.add_argument("--log-every-min", type=float, default=10.0, help="đẩy log tối đa mỗi N phút (luôn đẩy khi dừng/lỗi)")
    p.add_argument("--log-workdir", default=None, help=argparse.SUPPRESS)
    p.add_argument("--smoke", action="store_true", help="CPU + dữ liệu giả + vài step: kiểm tra trước khi push")
    p.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE", help="ghi đè config, vd train.lr=0.05")
    return p.parse_args(argv)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def build_optimizer(cfg, model):
    t = cfg["train"]
    if t["optimizer"] == "sgd":
        return torch.optim.SGD(model.parameters(), lr=t["lr"], momentum=0.9, nesterov=True,
                               weight_decay=t["weight_decay"])
    if t["optimizer"] == "adamw":
        return torch.optim.AdamW(model.parameters(), lr=t["lr"], weight_decay=t["weight_decay"])
    raise ValueError(f"Optimizer không hỗ trợ: {t['optimizer']!r} (có: sgd, adamw)")


def resolve_resume(args, ckpt_dir):
    if args.resume == "none":
        return None
    if args.resume != "auto":
        return args.resume
    ck = latest_ckpt(ckpt_dir)
    if ck is None and args.hub_repo:
        from src.utils import hub_sync
        ck = hub_sync.pull(args.hub_repo, args.run_name, ckpt_dir)
    return ck


@torch.no_grad()
def evaluate(model, loader, device, use_amp):
    model.eval()
    loss_sum = correct = n = 0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=use_amp):
            out = model(x)
        loss_sum += F.cross_entropy(out.float(), y, reduction="sum").item()
        correct += (out.argmax(1) == y).sum().item()
        n += y.size(0)
    return loss_sum / n, correct / n


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):      # console Windows mặc định cp1252, không in được tiếng Việt
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    ckpt_dir = args.ckpt_dir or os.path.join(default_path("ckpt"), args.run_name)
    os.makedirs(ckpt_dir, exist_ok=True)
    logger = NullLogger()
    if args.log_branch:
        logger = RunLogger(args.run_name, ckpt_dir, branch=args.log_branch, remote=args.log_remote,
                           every_min=args.log_every_min, workdir=args.log_workdir)
    try:
        run(args, ckpt_dir, logger)
    except (Exception, KeyboardInterrupt) as e:       # KeyboardInterrupt: bấm Interrupt/Stop trên Colab
        logger.finish("interrupted" if isinstance(e, KeyboardInterrupt) else "error", traceback.format_exc())
        raise
    finally:
        logger.close()


def run(args, ckpt_dir, logger):
    cfg = load_config(args.config, args.set)
    if args.smoke:
        cfg["train"].update(cfg["smoke"])
        cfg["data"]["num_workers"] = 0
    data_dir = args.data_dir or default_path("data")
    device = torch.device("cuda" if torch.cuda.is_available() and not args.smoke else "cpu")
    use_amp = device.type == "cuda" and cfg["train"].get("amp", True)
    commit = git_commit()
    print(f"[env] {detect_env()} | device={device} | amp={use_amp} | commit={commit} | ckpt_dir={ckpt_dir}")

    set_seed(cfg["seed"])
    train_ds, val_ds = build_datasets(cfg, data_dir, args.smoke)
    num_workers = cfg["data"].get("num_workers", 2)
    val_loader = make_val_loader(val_ds, cfg, num_workers)
    steps_per_epoch = len(train_ds) // cfg["train"]["batch_size"]
    total_steps = steps_per_epoch * cfg["train"]["epochs"]

    model = build_model(cfg).to(device)
    opt = build_optimizer(cfg, model)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=cfg["train"]["lr"], total_steps=total_steps,
                                                pct_start=cfg["train"].get("warmup_pct", 0.15))
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    criterion = nn.CrossEntropyLoss(label_smoothing=cfg["train"].get("label_smoothing", 0.0))

    state = {"epoch": 0, "step": 0, "best_acc": 0.0, "train_time_s": 0.0}
    ck = resolve_resume(args, ckpt_dir)
    if ck:
        s = load_ckpt(ck)
        model.load_state_dict(s["model"])
        opt.load_state_dict(s["optimizer"])
        sched.load_state_dict(s["scheduler"])
        if s["scaler"]:                      # ckpt tạo trên CPU có scaler rỗng
            scaler.load_state_dict(s["scaler"])
        set_rng_state(s["rng"])
        state = {k: s[k] for k in state}
        if s["git_commit"] != commit:
            print(f"[CẢNH BÁO] ckpt tạo từ commit {s['git_commit']}, code hiện tại là {commit}")
        print(f"[resume] {ck} → epoch {state['epoch']}, step {state['step']}/{total_steps}")
    else:
        print(f"[start] train từ đầu: {cfg['train']['epochs']} epoch × {steps_per_epoch} step")

    logger.update(status="running", platform=detect_env(), config=args.config, git_commit=commit,
                  gpu=torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
                  epoch=state["epoch"], total_epochs=cfg["train"]["epochs"], step=state["step"],
                  total_steps=total_steps, best_val_acc=round(state["best_acc"], 4))
    if state["epoch"] >= cfg["train"]["epochs"]:
        print("[done] Run này đã train xong. Đổi --run-name nếu muốn chạy run mới.")
        logger.finish("done")
        return
    logger.push(f"start at epoch {state['epoch']}")

    t0 = last_save = time.time()

    def train_time_s():
        return state["train_time_s"] + (time.time() - t0)

    def save(tag):
        path = save_ckpt(ckpt_dir, {
            "model": model.state_dict(), "optimizer": opt.state_dict(), "scheduler": sched.state_dict(),
            "scaler": scaler.state_dict(), "rng": rng_state(), "config": cfg, "git_commit": commit,
            **state, "train_time_s": train_time_s(),
        }, keep_last=cfg["train"].get("keep_last", 2))
        print(f"[ckpt:{tag}] {path}")
        if args.hub_repo:
            try:
                from src.utils import hub_sync
                hub_sync.push(path, args.hub_repo, args.run_name, name="last.pt")
            except Exception as e:           # mất mạng không được làm hỏng run đang train
                print(f"[hub] không đẩy được ckpt: {type(e).__name__}: {e}")
        return path

    session_steps = 0
    budget_s = args.time_budget_h * 3600
    while state["epoch"] < cfg["train"]["epochs"]:
        epoch = state["epoch"]
        skip = state["step"] - epoch * steps_per_epoch   # số batch của epoch này đã train trước khi bị ngắt
        loader = make_train_loader(train_ds, cfg, epoch, skip, num_workers)
        model.train()
        loss_sum = correct = seen = 0
        for x, y in loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device_type=device.type, enabled=use_amp):
                out = model(x)
                loss = criterion(out, y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            state["step"] += 1
            session_steps += 1
            loss_sum += loss.item() * y.size(0)
            correct += (out.argmax(1) == y).sum().item()
            seen += y.size(0)
            if state["step"] % cfg["train"].get("log_every", 100) == 0:
                print(f"  step {state['step']}/{total_steps} | loss {loss_sum / seen:.4f} | "
                      f"acc {correct / seen:.4f} | lr {sched.get_last_lr()[0]:.5f}")
            if time.time() - t0 > budget_s or (args.max_steps and session_steps >= args.max_steps):
                save("time-budget")
                print("[time-budget] Đã dừng sạch. Chạy lại đúng lệnh này (giữ --run-name) để train tiếp.")
                logger.update(step=state["step"], train_time_min=round(train_time_s() / 60, 1))
                logger.finish("stopped-time-budget")
                return
            if time.time() - last_save > args.save_every_min * 60:
                save("periodic")
                last_save = time.time()

        val_loss, val_acc = evaluate(model, val_loader, device, use_amp)
        state["epoch"] = epoch + 1
        if val_acc > state["best_acc"]:
            state["best_acc"] = val_acc
            torch.save({"model": model.state_dict(), "val_acc": val_acc, "epoch": epoch + 1,
                        "config": cfg, "git_commit": commit}, os.path.join(ckpt_dir, "best.pt"))
        save("epoch")
        last_save = time.time()
        metrics_path = append_metrics(ckpt_dir, {
            "epoch": epoch + 1, "step": state["step"],
            "train_loss": round(loss_sum / max(seen, 1), 4), "train_acc": round(correct / max(seen, 1), 4),
            "val_loss": round(val_loss, 4), "val_acc": round(val_acc, 4),
            "lr": round(sched.get_last_lr()[0], 6), "train_time_min": round(train_time_s() / 60, 1),
            "git_commit": commit,
        })
        print(f"[epoch {epoch + 1}/{cfg['train']['epochs']}] val_loss {val_loss:.4f} | val_acc {val_acc:.4f} "
              f"| best {state['best_acc']:.4f}")
        eta_min = (time.time() - t0) / max(session_steps, 1) * (total_steps - state["step"]) / 60
        logger.update(epoch=epoch + 1, step=state["step"], val_acc=round(val_acc, 4), val_loss=round(val_loss, 4),
                      train_loss=round(loss_sum / max(seen, 1), 4), best_val_acc=round(state["best_acc"], 4),
                      train_time_min=round(train_time_s() / 60, 1), eta_min=round(eta_min, 1))
        logger.maybe_push(f"epoch {epoch + 1}/{cfg['train']['epochs']} val_acc {val_acc:.4f}")

    summary = {"run_name": args.run_name, "epochs": state["epoch"], "steps": state["step"],
               "best_val_acc": round(state["best_acc"], 4), "last_val_acc": round(val_acc, 4),
               "train_time_min": round(train_time_s() / 60, 1), "git_commit": commit, "config": cfg}
    summary_path = os.path.join(ckpt_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    if args.hub_repo:
        try:
            from src.utils import hub_sync
            for p in (metrics_path, summary_path):
                hub_sync.push(p, args.hub_repo, args.run_name)
        except Exception as e:
            print(f"[hub] không đẩy được kết quả: {type(e).__name__}: {e}")
    print(f"[done] best val_acc {state['best_acc']:.4f} | {summary['train_time_min']} phút | {summary_path}")
    logger.update(eta_min=0)
    logger.finish("done")


if __name__ == "__main__":
    main()
