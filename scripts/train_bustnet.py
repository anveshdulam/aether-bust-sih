"""
Train BustNet on the synthetic corpus.

Contracts honoured verbatim (nothing here modifies Phase 1 or Phase 2):
  * `BustNet` and `MultiTaskBustLoss` are imported unchanged.
  * Input tensors are exactly [B, 10, 10, 128, 128] float32 (TRD 2.2).
  * Normalization follows TRD 2.2.1: log1p on the tp channel, then the fixed
    per-channel MU/SIGMA from `app/ml/norm_stats.json`.
  * The checkpoint is a BARE state_dict, which is what `InferenceRunner.load()`
    expects (and what `torch.load(weights_only=True)` accepts on torch >= 2.6).

Deliberately does NOT import `app.ml.inference`: that module runs
`torch.use_deterministic_algorithms(True)` and `torch.set_num_threads(1)` at
import time, which would force deterministic-only CUDA kernels and throttle the
dataloader.

Examples
--------
  # smoke test: 4 runs, 2 steps, CPU
  python scripts/train_bustnet.py --smoke

  # Kaggle T4
  python scripts/train_bustnet.py --data-dir /kaggle/working/data --n-runs 256 \
      --epochs 30 --batch-size 4 --amp --device cuda \
      --out /kaggle/working/bustnet.pt
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.constants import C, H, SEED, T, V, VAR_CODES, W  # noqa: E402
from app.ml.architecture import BustNet  # noqa: E402
from app.ml.loss import MultiTaskBustLoss  # noqa: E402
from data.generator import canonical_norm_stats, generate_dataset  # noqa: E402

DEFAULT_NORM_STATS = BACKEND / "app" / "ml" / "norm_stats.json"


# ------------------------------------------------------------------ dataset


class BustRunDataset(Dataset):
    """
    One synthetic forecast run per item.

    Returns (X[10,10,128,128], Yb[10,4,128,128], Ye[10,4,128,128]), all float32,
    with X already normalized per TRD 2.2.1.
    """

    def __init__(self, run_dirs, mu, sigma):
        self.run_dirs = [Path(d) for d in run_dirs]
        self.mu = np.asarray(mu, dtype=np.float32).reshape(1, C, 1, 1)
        self.sigma = np.asarray(sigma, dtype=np.float32).reshape(1, C, 1, 1)
        self.sigma = np.where(np.abs(self.sigma) < 1e-8, np.float32(1.0), self.sigma)

    def __len__(self):
        return len(self.run_dirs)

    def __getitem__(self, idx):
        d = self.run_dirs[idx]
        X = np.load(d / "X.npy").astype(np.float32)[0]  # [T, C, H, W]
        Yb = np.load(d / "Yb_true.npy").astype(np.float32)
        Ye = np.load(d / "Ye_true.npy").astype(np.float32)

        # TRD 2.2.1: precipitation is log1p-transformed before standardization.
        X[:, 1] = np.log1p(np.maximum(X[:, 1], 0.0))
        X = (X - self.mu) / self.sigma

        return torch.from_numpy(X), torch.from_numpy(Yb), torch.from_numpy(Ye)


def load_norm_stats(path) -> tuple[np.ndarray, np.ndarray]:
    p = Path(path)
    if p.is_file():
        with open(p, encoding="utf-8") as fh:
            stats = json.load(fh)
    else:
        stats = canonical_norm_stats()
    mu = np.asarray(stats["MU"], dtype=np.float32)

    sigma = np.asarray(stats["SIGMA"], dtype=np.float32)
    if mu.shape != (C,) or sigma.shape != (C,):
        raise ValueError(f"norm_stats must hold {C}-length MU and SIGMA, got {mu.shape}/{sigma.shape}")
    return mu, sigma


# ------------------------------------------------------------------ metrics


@torch.no_grad()
def evaluate(model, loader, criterion, device, amp_dtype=None, max_batches=None):
    """Validation loss plus Brier score and base-rate comparison per variable."""
    model.eval()
    total_loss, n_batches = 0.0, 0
    sq_err = np.zeros(V, dtype=np.float64)
    pos = np.zeros(V, dtype=np.float64)
    count = np.zeros(V, dtype=np.float64)
    mae_reg = np.zeros(V, dtype=np.float64)

    for bi, (X, Yb, Ye) in enumerate(loader):
        if max_batches is not None and bi >= max_batches:
            break
        X, Yb, Ye = X.to(device), Yb.to(device), Ye.to(device)

        if amp_dtype is not None:
            with torch.autocast(device_type=device.type, dtype=amp_dtype):
                out = model(X)
            bust = out["bust"].float()
            err = out["error"].float()
        else:
            out = model(X)
            bust, err = out["bust"], out["error"]

        total_loss += float(criterion(bust, err, Yb, Ye))
        n_batches += 1

        b = bust.detach().cpu().numpy()
        yb = Yb.detach().cpu().numpy()
        e = err.detach().cpu().numpy()
        ye = Ye.detach().cpu().numpy()
        for v in range(V):
            sq_err[v] += float(((b[:, :, v] - yb[:, :, v]) ** 2).sum())
            pos[v] += float(yb[:, :, v].sum())
            count[v] += yb[:, :, v].size
            mae_reg[v] += float(np.abs(e[:, :, v] - ye[:, :, v]).sum())

    brier = sq_err / np.maximum(count, 1)
    base = pos / np.maximum(count, 1)
    # Brier score of always predicting the base rate -- the bar a model must beat.
    brier_base = base * (1.0 - base)
    return {
        "loss": total_loss / max(n_batches, 1),
        "brier": brier,
        "base_rate": base,
        "brier_baseline": brier_base,
        "skill_vs_baseline": 1.0 - brier / np.maximum(brier_base, 1e-12),
        "mae_reg": mae_reg / np.maximum(count, 1),
    }


def fmt_per_var(values) -> str:
    return "  ".join(f"{v}={values[i]:.4f}" for i, v in enumerate(VAR_CODES))


# ------------------------------------------------------------------ training


def resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested but torch.cuda.is_available() is False")
    return torch.device(requested)


def resolve_amp_dtype(device: torch.device, enabled: bool):
    """
    fp16 on CUDA: Tesla T4 is compute capability 7.5 -- fp16 tensor cores, NO
    bf16. bf16 on a T4 either errors or silently emulates.
    bf16 on CPU: fp16 autocast on CPU is slow and poorly supported.
    """
    if not enabled:
        return None
    if device.type == "cuda":
        return torch.float16
    return torch.bfloat16


def train(args) -> int:
    torch.manual_seed(args.seed)
    np.random.seed(args.seed % (2**32))

    device = resolve_device(args.device)
    amp_dtype = resolve_amp_dtype(device, args.amp)

    print(f"torch {torch.__version__}  device={device}  amp={amp_dtype}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"gpu: {props.name}  sm_{props.major}{props.minor}  "
              f"{props.total_memory / 1024**3:.2f} GiB")
        if amp_dtype is torch.float16 and props.major < 7:
            print("warning: fp16 tensor cores need sm_70+; AMP will be slow here")

    # --- data ---------------------------------------------------------
    data_dir = Path(args.data_dir)
    t0 = time.perf_counter()
    run_dirs = generate_dataset(str(data_dir), args.n_runs, prefix=args.prefix)
    print(f"dataset: {len(run_dirs)} runs under {data_dir} "
          f"({time.perf_counter() - t0:.1f}s)")

    mu, sigma = load_norm_stats(args.norm_stats)

    n_val = max(1, int(round(len(run_dirs) * args.val_frac)))
    # Deterministic split: the run ids are ordered, so the tail is the val set.
    train_dirs, val_dirs = run_dirs[:-n_val], run_dirs[-n_val:]
    if not train_dirs:
        raise SystemExit("not enough runs for a train split; raise --n-runs")
    print(f"split: {len(train_dirs)} train / {len(val_dirs)} val")

    train_ds = BustRunDataset(train_dirs, mu, sigma)
    val_ds = BustRunDataset(val_dirs, mu, sigma)

    loader_kw = dict(num_workers=args.num_workers, pin_memory=(device.type == "cuda"))
    if args.num_workers > 0:
        loader_kw["persistent_workers"] = True
        loader_kw["prefetch_factor"] = 2
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              drop_last=False, **loader_kw)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            drop_last=False, **loader_kw)

    # --- model --------------------------------------------------------
    model = BustNet().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"BustNet params: {n_params:,} ({n_params * 4 / 1024**2:.1f} MB fp32)")

    criterion = MultiTaskBustLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr,
                                  weight_decay=args.weight_decay)
    steps_per_epoch = max(1, len(train_loader))
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=args.lr, total_steps=args.epochs * steps_per_epoch,
        pct_start=0.15,
    )
    scaler = torch.amp.GradScaler(device.type, enabled=(amp_dtype is torch.float16))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    best_val = float("inf")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running, n_steps = 0.0, 0
        epoch_start = time.perf_counter()

        for bi, (X, Yb, Ye) in enumerate(train_loader):
            if args.limit_steps and bi >= args.limit_steps:
                break
            X = X.to(device, non_blocking=True)
            Yb = Yb.to(device, non_blocking=True)
            Ye = Ye.to(device, non_blocking=True)

            if X.shape[1:] != (T, C, H, W):
                raise ValueError(f"batch violates the TRD 2.2 contract: {tuple(X.shape)}")

            optimizer.zero_grad(set_to_none=True)

            # Only the FORWARD pass is autocast. The loss must run in fp32:
            # F.binary_cross_entropy is on PyTorch's autocast-unsafe list and
            # raises under autocast, so `loss.py` stays untouched and we cast
            # the heads back to fp32 before calling it.
            if amp_dtype is not None:
                with torch.autocast(device_type=device.type, dtype=amp_dtype):
                    out = model(X)
                loss = criterion(out["bust"].float(), out["error"].float(), Yb, Ye)
            else:
                out = model(X)
                loss = criterion(out["bust"], out["error"], Yb, Ye)

            if not torch.isfinite(loss):
                raise SystemExit(f"loss became {loss.item()} at epoch {epoch} step {bi}")

            scaler.scale(loss).backward()
            if args.grad_clip > 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            scaler.step(optimizer)
            scaler.update()
            if scheduler.last_epoch < scheduler.total_steps - 1:
                scheduler.step()

            running += float(loss.detach())
            n_steps += 1

        train_loss = running / max(n_steps, 1)
        val = evaluate(model, val_loader, criterion, device, amp_dtype,
                       max_batches=args.limit_steps or None)
        dt = time.perf_counter() - epoch_start

        peak = ""
        if device.type == "cuda":
            peak = f"  peak_vram={torch.cuda.max_memory_allocated() / 1024**3:.2f}GiB"
        print(f"epoch {epoch:3d}/{args.epochs}  train_loss={train_loss:.4f}  "
              f"val_loss={val['loss']:.4f}  {dt:.1f}s{peak}")
        print(f"            brier      {fmt_per_var(val['brier'])}")
        print(f"            vs base    {fmt_per_var(val['skill_vs_baseline'])}")

        if val["loss"] < best_val:
            best_val = val["loss"]
            torch.save(model.state_dict(), out_path)
            print(f"            saved -> {out_path}")

    print(f"\nbest val_loss={best_val:.4f}")
    print(f"checkpoint: {out_path}")
    print("point MODEL_WEIGHTS_PATH at it to serve the trained model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train BustNet on the synthetic corpus")
    p.add_argument("--data-dir", default=str(BACKEND / "artifacts" / "train"),
                   help="where synthetic runs are materialized (reused if present)")
    p.add_argument("--n-runs", type=int, default=256)
    p.add_argument("--prefix", default="syn")
    p.add_argument("--val-frac", type=float, default=0.15)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-2)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--amp", action="store_true",
                   help="mixed precision (fp16 on CUDA, bf16 on CPU)")
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--norm-stats", default=str(DEFAULT_NORM_STATS))
    p.add_argument("--out", default=str(BACKEND / "app" / "ml" / "weights" / "bustnet.pt"))
    p.add_argument("--limit-steps", type=int, default=0,
                   help="cap batches per epoch (smoke testing)")
    p.add_argument("--smoke", action="store_true",
                   help="tiny end-to-end run: 4 runs, 1 epoch, 2 steps, batch 1")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke:
        args.n_runs = max(args.n_runs if args.n_runs < 4 else 4, 3)
        args.epochs = 1
        args.limit_steps = 2
        args.batch_size = min(args.batch_size, 2)
        args.num_workers = 0
        args.val_frac = 0.34
        args.data_dir = str(Path(args.data_dir).parent / "smoke")
        args.out = str(Path(args.out).parent / "bustnet_smoke.pt")
        print("=== SMOKE MODE ===")
    return train(args)


if __name__ == "__main__":
    raise SystemExit(main())
