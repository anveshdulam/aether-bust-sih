"""Generate AETHER-BUST architecture flow diagram (dark theme) as PNG."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 870
BG = (13, 17, 23)          # dark surface (github-dark-ish)
CARD = (22, 27, 34)        # card fill
CARD_BORDER = (48, 56, 66)
ACCENT = (88, 166, 255)    # sequential hue - blue (identity: pipeline stage)
ACCENT_2 = (63, 185, 133)  # green - outputs
ACCENT_3 = (240, 136, 62)  # orange/amber - XAI / explainability
TEXT_PRIMARY = (230, 237, 243)
TEXT_SECONDARY = (139, 148, 158)
ARROW = (110, 118, 129)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def f(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def text_centered(cx, cy, s, font, fill):
    bbox = d.textbbox((0, 0), s, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2, cy - th / 2 - bbox[1]), s, font=font, fill=fill)

def rounded_card(x0, y0, x1, y1, fill, border, radius=14, width=2):
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=border, width=width)

def arrow(x0, y0, x1, y1, color=ARROW, width=3):
    d.line([x0, y0, x1, y1], fill=color, width=width)
    # arrowhead
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    ah = 10
    p1 = (x1 - ah * math.cos(ang - 0.4), y1 - ah * math.sin(ang - 0.4))
    p2 = (x1 - ah * math.cos(ang + 0.4), y1 - ah * math.sin(ang + 0.4))
    d.polygon([p1, (x1, y1), p2], fill=color)

# Title
text_centered(W / 2, 40, "AETHER-BUST — System Architecture", f(30, bold=True), TEXT_PRIMARY)
text_centered(W / 2, 75, "SIH26079 · AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts", f(15), TEXT_SECONDARY)

# ---- Row 1: Input ----
y0 = 120
rounded_card(60, y0, 380, y0 + 90, CARD, ACCENT)
text_centered(220, y0 + 30, "Input Tensor X", f(17, bold=True), TEXT_PRIMARY)
text_centered(220, y0 + 60, "[B,10,10,128,128]  10 channels x 10 days", f(12), TEXT_SECONDARY)

arrow(380, y0 + 45, 440, y0 + 45)

# U-Net Encoder
rounded_card(440, y0, 760, y0 + 90, CARD, ACCENT)
text_centered(600, y0 + 30, "U-Net Spatial Encoder", f(17, bold=True), TEXT_PRIMARY)
text_centered(600, y0 + 60, "shared weights per timestep, 4 skip levels", f(12), TEXT_SECONDARY)

arrow(760, y0 + 45, 820, y0 + 45)

# ConvLSTM
rounded_card(820, y0, 1140, y0 + 90, CARD, ACCENT)
text_centered(980, y0 + 30, "ConvLSTM (Temporal)", f(17, bold=True), TEXT_PRIMARY)
text_centered(980, y0 + 60, "causal recurrence across Day 1..10", f(12), TEXT_SECONDARY)

arrow(1140, y0 + 45, 1200, y0 + 45)

# Self-Attention
rounded_card(1200, y0, 1540, y0 + 90, CARD, ACCENT)
text_centered(1370, y0 + 30, "Temporal Self-Attention", f(17, bold=True), TEXT_PRIMARY)
text_centered(1370, y0 + 60, "8-head, causal mask, per grid cell", f(12), TEXT_SECONDARY)

# down arrow to decoder
arrow(1370, y0 + 90, 1370, y0 + 150)

# ---- Row 2: Decoder ----
y1 = 250
rounded_card(1040, y1, 1540, y1 + 90, CARD, ACCENT)
text_centered(1290, y1 + 30, "U-Net Spatial Decoder", f(17, bold=True), TEXT_PRIMARY)
text_centered(1290, y1 + 60, "skip connections restored, per timestep", f(12), TEXT_SECONDARY)

arrow(1040, y1 + 45, 760, y1 + 45)

# Output heads
rounded_card(440, y1, 760, y1 + 90, CARD, ACCENT_2)
text_centered(600, y1 + 22, "Output Heads", f(17, bold=True), TEXT_PRIMARY)
text_centered(600, y1 + 46, "Bust Head (sigmoid) -> Yb", f(12), TEXT_SECONDARY)
text_centered(600, y1 + 66, "Error Head (softplus) -> Ye", f(12), TEXT_SECONDARY)

arrow(440, y1 + 45, 380, y1 + 45)

# Confidence Index
rounded_card(60, y1, 380, y1 + 90, CARD, ACCENT_2)
text_centered(220, y1 + 30, "Confidence Index C", f(17, bold=True), TEXT_PRIMARY)
text_centered(220, y1 + 60, "deterministic post-process, 0-100 scale", f(12), TEXT_SECONDARY)

# down arrows to row 3
arrow(220, y1 + 90, 220, y1 + 150)
arrow(600, y1 + 90, 600, y1 + 150)

# ---- Row 3: XAI + Masking ----
y2 = 380
rounded_card(60, y2, 380, y2 + 90, CARD, ACCENT_3)
text_centered(220, y2 + 22, "XAI Module", f(17, bold=True), TEXT_PRIMARY)
text_centered(220, y2 + 46, "Grad-CAM (where) + SHAP/IG (why)", f(12), TEXT_SECONDARY)
text_centered(220, y2 + 66, "10 ranked meteorological drivers", f(12), TEXT_SECONDARY)

rounded_card(440, y2, 760, y2 + 90, CARD, ACCENT_3)
text_centered(600, y2 + 22, "Bust Masking", f(17, bold=True), TEXT_PRIMARY)
text_centered(600, y2 + 46, "connected components on P_agg >= 0.5", f(12), TEXT_SECONDARY)
text_centered(600, y2 + 66, "bbox + polygon per blob", f(12), TEXT_SECONDARY)

arrow(380, y2 + 45, 440, y2 + 45)
arrow(220, y2 + 90, 220, y2 + 150)
arrow(600, y2 + 90, 600, y2 + 150)

# ---- Row 4: Persistence + API ----
y3 = 510
rounded_card(60, y3, 380, y3 + 90, CARD, CARD_BORDER)
text_centered(220, y3 + 22, "MongoDB", f(17, bold=True), TEXT_PRIMARY)
text_centered(220, y3 + 46, "forecast_runs, bust_detections,", f(12), TEXT_SECONDARY)
text_centered(220, y3 + 66, "telemetry, baselines", f(12), TEXT_SECONDARY)

arrow(380, y3 + 45, 440, y3 + 45)

rounded_card(440, y3, 760, y3 + 90, CARD, CARD_BORDER)
text_centered(600, y3 + 22, "FastAPI REST Layer", f(17, bold=True), TEXT_PRIMARY)
text_centered(600, y3 + 46, "/confidence-map /bust-probability", f(11), TEXT_SECONDARY)
text_centered(600, y3 + 66, "/attribution /export /telemetry", f(11), TEXT_SECONDARY)

arrow(760, y3 + 45, 820, y3 + 45)

# Split to dashboard and export
rounded_card(820, y3, 1140, y3 + 90, CARD, CARD_BORDER)
text_centered(980, y3 + 22, "Ops Dashboard (React)", f(17, bold=True), TEXT_PRIMARY)
text_centered(980, y3 + 46, "map + Day1-10 scrubber", f(12), TEXT_SECONDARY)
text_centered(980, y3 + 66, "+ attribution panel", f(12), TEXT_SECONDARY)

rounded_card(1200, y3, 1540, y3 + 90, CARD, CARD_BORDER)
text_centered(1370, y3 + 22, "Export & Alerts", f(17, bold=True), TEXT_PRIMARY)
text_centered(1370, y3 + 46, "GeoJSON / GeoTIFF / NetCDF", f(12), TEXT_SECONDARY)
text_centered(1370, y3 + 66, "threshold-based bust alerts", f(12), TEXT_SECONDARY)

arrow(1140, y3 + 45, 1200, y3 + 45)

# Legend
ly = 630
d.rectangle([60, ly, 80, ly + 20], fill=ACCENT)
d.text((90, ly + 2), "Model pipeline (BustNet)", font=f(13), fill=TEXT_SECONDARY)
d.rectangle([320, ly, 340, ly + 20], fill=ACCENT_2)
d.text((350, ly + 2), "Outputs (bust prob / error / confidence)", font=f(13), fill=TEXT_SECONDARY)
d.rectangle([680, ly, 700, ly + 20], fill=ACCENT_3)
d.text((710, ly + 2), "Explainability (XAI)", font=f(13), fill=TEXT_SECONDARY)
d.rectangle([920, ly, 940, ly + 20], outline=CARD_BORDER, width=2)
d.text((950, ly + 2), "Serving / operational layer", font=f(13), fill=TEXT_SECONDARY)

# Bottom: bust math strip
by0 = 690
rounded_card(60, by0, 1540, by0 + 130, (17, 21, 28), CARD_BORDER, radius=10)
text_centered(W / 2, by0 + 24, "Bust Definition & Confidence Formula", f(16, bold=True), TEXT_PRIMARY)
text_centered(W / 2, by0 + 55, "B_v(t,i,j) = 1  if  |F_v - A_v| > tau_v      (tau: t2m=3.0K, tp=20mm/24h, z500=60gpm, ws850=5m/s)", f(13), TEXT_SECONDARY)
text_centered(W / 2, by0 + 82, "C(t,i,j) = 100 * (1 - sum_v w_v * p_v(t,i,j))      w: t2m=0.25, tp=0.35, z500=0.25, ws850=0.15", f(13), TEXT_SECONDARY)
text_centered(W / 2, by0 + 109, "Ground truth A = ERA5 reanalysis   |   Forecast F = GFS/ECMWF (synthetic generator in v1.0)", f(12), TEXT_SECONDARY)

# Footer
text_centered(W / 2, H - 25, "AETHER-BUST v1.0.0  |  Ministry of Earth Sciences  |  SIH 2026", f(12), TEXT_SECONDARY)

out_path = "/home/anvesh/Pictures/sih hackathon idea 2/architecture_diagram.png"
img.save(out_path)
print("saved:", out_path)
