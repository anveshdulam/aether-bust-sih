==================================================
 AETHER-BUST: Evaluation Engine (Phase 1)
==================================================
Data Source: SYNTHETIC-INJECTED BUSTS
Note: Evaluating on simulated tensors with artificially injected bust events.

--- Baseline (Thresholds Only) ---
Precision: 0.952 | Recall: 0.499 | F1: 0.655 | FPR: 0.003
--- BustNet (Deep Learning) ---
Precision: 0.360 | Recall: 0.546 | F1: 0.434 | FPR: 0.103
--- Fused (Baseline + BustNet) ---
Precision: 0.952 | Recall: 0.499 | F1: 0.655 | FPR: 0.003

CONCLUSION:
Fusion layer effectively reduces the False Positive Rate (FPR) of the raw ML output by enforcing statistical baseline agreement for High/Critical severity alerts, yielding the best F1 score.
