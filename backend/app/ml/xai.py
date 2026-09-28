import torch
import numpy as np
from captum.attr import IntegratedGradients
from app.constants import CHANNEL_CODES, C, H, W

# Integrated Gradients on a [1,10,10,128,128] input is memory-bound on CPU:
# Captum expands the input by `n_steps` along the batch dim, and every expanded
# sample retains the full U-Net activation stack for all 10 lead times. These
# defaults keep the Riemann approximation meaningful while holding one sample in
# memory at a time.
IG_N_STEPS = 8
IG_INTERNAL_BATCH_SIZE = 1


def _as_mask(region_mask, like):
    """region_mask -> float tensor [128,128] on the same device/dtype as `like`."""
    if region_mask is None:
        return torch.ones((H, W), device=like.device, dtype=like.dtype)
    return torch.as_tensor(np.asarray(region_mask, dtype=np.float32),
                           device=like.device, dtype=like.dtype)


def gradcam(model, X, v, t, region_mask=None):
    """
    Grad-CAM over the final decoder block (TRD 2.5).

    X: [1, 10, 10, 128, 128]
    v: variable index, t: lead time index
    region_mask: optional boolean/float mask [128, 128] for regional pooling
    Returns: [128, 128] float32 array in [0, 1]
    """
    model.eval()
    X = X.detach().clone().requires_grad_(True)

    # The decoder runs once per lead time, so hooks fire T times per forward
    # pass. Key the captured tensors by call index and grab the grad off the
    # activation itself -- a module backward hook only fires for the single
    # decoder call that `score` actually depends on, which makes positional
    # indexing into a flat list unsound.
    acts, grads, call_idx = {}, {}, {"i": 0}

    def forward_hook(module, inputs, output):
        i = call_idx["i"]
        call_idx["i"] += 1
        acts[i] = output
        if output.requires_grad:
            output.register_hook(lambda g, i=i: grads.__setitem__(i, g))

    handle = model.decoder.conv1.register_forward_hook(forward_hook)
    try:
        Yb = model(X)["bust"]
        mask = _as_mask(region_mask, X)
        denom = mask.sum().clamp(min=1.0)
        score = (Yb[0, t, v] * mask).sum() / denom

        model.zero_grad(set_to_none=True)
        score.backward()
    finally:
        handle.remove()

    if t not in acts or t not in grads:
        raise RuntimeError(f"Grad-CAM did not capture decoder activations for lead time {t}")

    act, grad = acts[t], grads[t]                      # [1, 64, 128, 128]
    weights = grad.mean(dim=(2, 3), keepdim=True)      # [1, 64, 1, 1]
    cam = torch.relu((weights * act).sum(dim=1)[0])    # [128, 128]

    cam_min, cam_max = cam.min(), cam.max()
    if cam_max > cam_min:
        cam = (cam - cam_min) / (cam_max - cam_min)
    else:
        # Flat CAM carries no localisation signal; report an empty map rather
        # than an unnormalised constant that could fall outside [0, 1].
        cam = torch.zeros_like(cam)

    return cam.detach().cpu().numpy().astype(np.float32)


def integrated_gradients(model, X, v, t, region_mask, n_steps=IG_N_STEPS):
    """
    Per-channel driver attribution via Integrated Gradients (TRD 2.5).

    Returns 10 dicts {code, score, sign} sorted by score desc, with scores
    L1-normalised so that sum(score) == 1.
    """
    model.eval()
    mask = _as_mask(region_mask, X)
    denom = mask.sum().clamp(min=1.0)

    def wrapper_func(X_in):
        Yb = model(X_in)["bust"]
        return ((Yb[:, t, v] * mask).sum(dim=(1, 2)) / denom).unsqueeze(1)

    ig = IntegratedGradients(wrapper_func)
    baseline = torch.zeros_like(X)  # normalised 0 == climatology
    attr = ig.attribute(
        X,
        baselines=baseline,
        target=0,
        n_steps=n_steps,
        internal_batch_size=IG_INTERNAL_BATCH_SIZE,
    )

    # attr: [1, 10, 10, 128, 128] -> collapse lead time and space per channel
    attr_masked = attr[0] * mask.view(1, 1, H, W)
    attr_ch_sum = attr_masked.sum(dim=(0, 2, 3))        # [10], signed
    attr_ch_abs = attr_masked.abs().sum(dim=(0, 2, 3))  # [10], magnitude

    total_abs = float(attr_ch_abs.sum())
    if total_abs > 0.0:
        scores = (attr_ch_abs / attr_ch_abs.sum()).tolist()
    else:
        # Degenerate case (e.g. input identical to the baseline): attribution is
        # undefined, so fall back to a uniform split rather than all-zeros, which
        # would break the sum-to-one contract.
        scores = [1.0 / C] * C

    drivers = [
        {
            "code": CHANNEL_CODES[c],
            "score": float(scores[c]),
            "sign": "+" if float(attr_ch_sum[c]) >= 0.0 else "-",
        }
        for c in range(C)
    ]

    # Re-normalise after the float() casts so the sum-to-one assertion holds exactly.
    total = sum(d["score"] for d in drivers)
    if total > 0.0:
        for d in drivers:
            d["score"] /= total

    drivers.sort(key=lambda x: x["score"], reverse=True)
    return drivers

def narrative(d, var_name, region_label, drivers):
    d1 = drivers[0]
    d2 = drivers[1]
    
    synoptic_clause = "Anomalous large-scale flow is elevating model uncertainty."
    if d1["code"] == "z500_anom" and d1["sign"] == "+":
        synoptic_clause = "A reinforced mid-tropospheric ridge is increasing model spread."
    elif d1["code"] == "cape":
        synoptic_clause = "Elevated convective instability raises precipitation-timing uncertainty."
    elif d1["code"] == "shear_850_250":
        synoptic_clause = "Strong deep-layer shear is associated with rapid synoptic evolution."
        
    return f"Day {d} bust risk for {var_name} over {region_label} is driven primarily by {d1['code']} ({int(d1['score']*100)}%, {d1['sign']}) and {d2['code']} ({int(d2['score']*100)}%, {d2['sign']}). {synoptic_clause}"
