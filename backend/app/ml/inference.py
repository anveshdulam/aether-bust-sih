import os
import json
from pathlib import Path

import numpy as np
import torch

from app.config import get_settings
from app.constants import SEED, T, C, H, W, V, VAR_CODES, W_CONF
from app.ml.architecture import BustNet
from app.ml.confidence import confidence_index
from app.ml.masking import extract_blobs


# Determinism block, executed at import (TRD 2.6).
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

torch.manual_seed(SEED)
torch.use_deterministic_algorithms(True)
torch.set_num_threads(int(os.environ.get("TORCH_NUM_THREADS", "1")))


# backend/app/ml/inference.py -> backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ARTIFACTS_ROOT = _BACKEND_ROOT / "artifacts"


class InferenceResult:
    """Outputs of one forecast-run inference (TRD 2.6 shapes)."""

    def __init__(self, bust, error, confidence, blobs):
        self.bust = bust
        # float32 [10, 4, 128, 128]

        self.error = error
        # float32 [10, 4, 128, 128]

        self.confidence = confidence
        # float32 [10, 128, 128]

        self.blobs = blobs
        # list[BustBlob], aggregate P_agg blobs


class InferenceRunner:

    def __init__(self, artifacts_root=None):
        self.model = None

        # Use CUDA when available, otherwise CPU.
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.weights_path = None

        self.artifacts_root = (
            Path(artifacts_root)
            if artifacts_root
            else _DEFAULT_ARTIFACTS_ROOT
        )

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self, weights_path=None):
        """
        Build BustNet and load the trained checkpoint.

        If weights_path is not explicitly supplied, the path is
        read from MODEL_WEIGHTS_PATH in the project's .env file.
        """

        torch.manual_seed(SEED)

        # Create the exact same BustNet architecture used during training.
        self.model = BustNet()

        # ---------------------------------------------------------
        # 1. Get checkpoint path
        # ---------------------------------------------------------
        if not weights_path:
            weights_path = get_settings().MODEL_WEIGHTS_PATH

        if not weights_path:
            raise RuntimeError(
                "MODEL_WEIGHTS_PATH is not configured."
            )

        weights_path = Path(weights_path)

        # ---------------------------------------------------------
        # 2. Resolve relative path
        # ---------------------------------------------------------
        if not weights_path.is_absolute():
            weights_path = _BACKEND_ROOT.parent / weights_path

        # ---------------------------------------------------------
        # 3. Verify checkpoint exists
        # ---------------------------------------------------------
        if not weights_path.exists():
            raise FileNotFoundError(
                f"BustNet checkpoint not found: {weights_path}"
            )

        # ---------------------------------------------------------
        # 4. Load trained weights
        # ---------------------------------------------------------
        state = torch.load(
            weights_path,
            map_location=self.device,
        )

        self.model.load_state_dict(state)

        self.weights_path = str(weights_path)

        # ---------------------------------------------------------
        # 5. Move model to GPU/CPU
        # ---------------------------------------------------------
        self.model.to(self.device)

        # ---------------------------------------------------------
        # 6. Evaluation mode
        # ---------------------------------------------------------
        self.model.eval()

        print(f"✅ BustNet loaded: {weights_path}")
        print(f"✅ Device: {self.device}")

        if self.device.type == "cuda":
            print(
                f"✅ GPU: {torch.cuda.get_device_name(0)}"
            )

    def warmup(self):

        if self.model is None:
            self.load()

        with torch.no_grad():
            self.model(
                torch.zeros(
                    1,
                    T,
                    C,
                    H,
                    W,
                    device=self.device,
                )
            )

    def run_dir(self, run_id: str) -> Path:
        return self.artifacts_root / run_id

    def normalize(
        self,
        X: np.ndarray,
        norm_stats_path=None,
    ) -> np.ndarray:
        """
        TRD 2.2.1:
        tp (channel 1) is log1p-transformed,
        then every channel is standardized with
        the fixed per-channel MU/SIGMA.
        """

        Xn = np.array(
            X,
            dtype=np.float32,
            copy=True,
        )

        # Transform precipitation channel.
        Xn[:, :, 1] = np.log1p(
            np.maximum(
                Xn[:, :, 1],
                0.0,
            )
        )

        mu = np.zeros(
            C,
            dtype=np.float32,
        )

        sigma = np.ones(
            C,
            dtype=np.float32,
        )

        if (
            norm_stats_path
            and os.path.exists(norm_stats_path)
        ):
            with open(
                norm_stats_path,
                "r",
                encoding="utf-8",
            ) as fh:

                stats = json.load(fh)

            mu = np.asarray(
                stats["MU"],
                dtype=np.float32,
            )

            sigma = np.asarray(
                stats["SIGMA"],
                dtype=np.float32,
            )

        sigma = np.where(
            np.abs(sigma) < 1e-8,
            np.float32(1.0),
            sigma,
        )

        return (
            (
                Xn
                - mu.reshape(
                    1,
                    1,
                    C,
                    1,
                    1,
                )
            )
            / sigma.reshape(
                1,
                1,
                C,
                1,
                1,
            )
        ).astype(np.float32)

    def ensure_inputs(
        self,
        run_id: str,
    ) -> Path:
        """
        Materialize the synthetic inputs for run_id
        if they are not on disk yet.
        """

        d = self.run_dir(run_id)

        if not (d / "X.npy").exists():

            from data.generator import generate_run

            d.mkdir(
                parents=True,
                exist_ok=True,
            )

            generate_run(
                run_id,
                str(d),
            )

        return d

    def run(
        self,
        run_id: str,
    ) -> InferenceResult:
        """
        Load X for run_id, infer, persist the output grids,
        and return the result.
        """

        d = self.ensure_inputs(run_id)

        X = np.load(
            d / "X.npy"
        ).astype(np.float32)

        X = self.normalize(
            X,
            norm_stats_path=d / "norm_stats.json",
        )

        result = self.run_tensor(X)

        np.save(
            d / "bust.npy",
            result.bust,
        )

        np.save(
            d / "error.npy",
            result.error,
        )

        np.save(
            d / "confidence.npy",
            result.confidence,
        )

        return result

    def run_tensor(
        self,
        X_npy: np.ndarray,
    ) -> InferenceResult:

        if self.model is None:
            self.load()

        with torch.no_grad():

            X_t = torch.as_tensor(
                np.asarray(
                    X_npy,
                    dtype=np.float32,
                ),
                device=self.device,
            )

            out = self.model(X_t)

            Yb = (
                out["bust"]
                .cpu()
                .numpy()[0]
            )
            # [10, 4, 128, 128]

            Ye = (
                out["error"]
                .cpu()
                .numpy()[0]
            )
            # [10, 4, 128, 128]

        conf = confidence_index(Yb)
        # [10, 128, 128]

        # P_agg(t) = sum_v w_v * p_v(t)
        # PRD 3.2 == 1 - C/100

        w = np.array(
            [
                W_CONF[v]
                for v in VAR_CODES
            ],
            dtype=np.float32,
        ).reshape(
            V,
            1,
            1,
        )

        blobs = []

        for t in range(T):

            for b in extract_blobs(
                np.sum(
                    w * Yb[t],
                    axis=0,
                )
            ):

                b.lead_time = t + 1

                blobs.append(b)

        return InferenceResult(
            Yb,
            Ye,
            conf,
            blobs,
        )