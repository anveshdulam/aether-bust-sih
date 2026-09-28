import torch
import torch.nn as nn
from app.constants import W_CONF, TAU, VAR_CODES

class MultiTaskBustLoss(nn.Module):
    def __init__(self, alpha=0.75, gamma=2.0, lam_hit=1.0, lam_all=0.1, beta_cls=1.0, beta_reg=0.5):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.lam_hit = lam_hit
        self.lam_all = lam_all
        self.beta_cls = beta_cls
        self.beta_reg = beta_reg
        self.w_v = torch.tensor([W_CONF[v] for v in VAR_CODES], dtype=torch.float32)
        self.tau = torch.tensor([TAU[v] for v in VAR_CODES], dtype=torch.float32)
        
    def forward(self, Yb_pred, Ye_pred, Yb_true, Ye_true):
        # Move weights to device
        device = Yb_pred.device
        w_v = self.w_v.to(device).view(1, 1, 4, 1, 1)
        tau = self.tau.to(device).view(1, 1, 4, 1, 1)
        
        # 1. Focal BCE
        bce = torch.nn.functional.binary_cross_entropy(Yb_pred, Yb_true, reduction='none')
        p_t = torch.where(Yb_true == 1, Yb_pred, 1 - Yb_pred)
        alpha_t = torch.where(Yb_true == 1, self.alpha, 1 - self.alpha)
        focal_weight = alpha_t * torch.pow(1 - p_t, self.gamma)
        
        l_cls_components = focal_weight * bce
        # Average over B, T, H, W for each variable
        l_cls_v = l_cls_components.mean(dim=(0, 1, 3, 4))
        
        # 2. Masked MAE
        Ye_pred_norm = Ye_pred / tau
        Ye_true_norm = Ye_true / tau
        
        mae = torch.abs(Ye_pred_norm - Ye_true_norm)
        
        # For hit mask, only where Yb_true == 1. To avoid zero division if no hits, sum and divide by count
        hit_mask = (Yb_true == 1).float()
        hit_counts = hit_mask.sum(dim=(0, 1, 3, 4))
        mae_hit = (mae * hit_mask).sum(dim=(0, 1, 3, 4)) / (hit_counts + 1e-8)
        
        mae_all = mae.mean(dim=(0, 1, 3, 4))
        
        l_reg_v = self.lam_hit * mae_hit + self.lam_all * mae_all
        
        # 3. Weighted sums
        L_cls_w = (w_v.squeeze() * l_cls_v).sum()
        L_reg_w = (w_v.squeeze() * l_reg_v).sum()
        
        L = self.beta_cls * L_cls_w + self.beta_reg * L_reg_w
        return L
