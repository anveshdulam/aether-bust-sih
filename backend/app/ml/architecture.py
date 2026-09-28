import torch
import torch.nn as nn
import torch.nn.functional as F
from app.constants import H, W, T, C, V

class ShapeContractError(ValueError):
    """Raised when a tensor violates the strict I/O contract of TRD 2.2."""

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class UNetEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = ConvBlock(C, 64)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(64, 128))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(128, 256))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(256, 256))
        self.down4 = nn.Sequential(nn.MaxPool2d(2), ConvBlock(256, 256))

    def forward(self, x):
        s1 = self.stem(x)
        s2 = self.down1(s1)
        s3 = self.down2(s2)
        s4 = self.down3(s3)
        bot = self.down4(s4)
        return bot, s1, s2, s3, s4

class ConvLSTMCell(nn.Module):
    def __init__(self, in_ch=256, hidden_ch=256, kernel_size=3):
        super().__init__()
        self.hidden_ch = hidden_ch
        padding = kernel_size // 2
        self.conv = nn.Conv2d(in_ch + hidden_ch, 4 * hidden_ch, kernel_size, padding=padding)

    def forward(self, x, state):
        h, c = state
        combined = torch.cat([x, h], dim=1)
        gates = self.conv(combined)
        i, f, o, g = torch.split(gates, self.hidden_ch, dim=1)
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        o = torch.sigmoid(o)
        g = torch.tanh(g)
        c_next = f * c + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

class TemporalSelfAttention(nn.Module):
    def __init__(self, d_model=256, nhead=8):
        super().__init__()
        self.mha = nn.MultiheadAttention(embed_dim=d_model, num_heads=nhead, batch_first=True)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, h_seq):
        # h_seq: [B, T, 256, 8, 8]
        B, T, C_, H_, W_ = h_seq.shape
        # Flatten spatial: [B, T, 256, 64] -> permute -> [B, 64, T, 256] -> merge B and spatial -> [B*64, T, 256]
        x = h_seq.view(B, T, C_, H_ * W_).permute(0, 3, 1, 2).reshape(B * H_ * W_, T, C_)
        
        causal_mask = torch.triu(torch.full((T, T), float('-inf'), device=x.device), diagonal=1)
        
        attn_out, _ = self.mha(x, x, x, attn_mask=causal_mask, need_weights=False)
        
        # Residual + Norm
        out = self.norm(x + attn_out)
        
        # Reshape back to [B, T, 256, 8, 8]
        out = out.view(B, H_ * W_, T, C_).permute(0, 2, 3, 1).view(B, T, C_, H_, W_)
        return out

class UNetDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.up4 = nn.ConvTranspose2d(256, 256, 2, stride=2)
        self.conv4 = ConvBlock(512, 256)
        
        self.up3 = nn.ConvTranspose2d(256, 256, 2, stride=2)
        self.conv3 = ConvBlock(512, 256)
        
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv2 = ConvBlock(256, 128)
        
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv1 = ConvBlock(128, 64)

    def forward(self, x, skips):
        s1, s2, s3, s4 = skips
        
        d = self.up4(x)
        d = self.conv4(torch.cat([d, s4], dim=1))
        
        d = self.up3(d)
        d = self.conv3(torch.cat([d, s3], dim=1))
        
        d = self.up2(d)
        d = self.conv2(torch.cat([d, s2], dim=1))
        
        d = self.up1(d)
        d = self.conv1(torch.cat([d, s1], dim=1))
        
        return d

class BustNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = UNetEncoder()
        self.lstm = ConvLSTMCell(256, 256)
        self.attn = TemporalSelfAttention(256, 8)
        self.decoder = UNetDecoder()
        
        self.head_bust = nn.Conv2d(64, V, kernel_size=1)
        self.head_error = nn.Conv2d(64, V, kernel_size=1)

    def forward(self, x):
        if x.shape[1:] != (T, C, H, W):
            raise ShapeContractError(f"Input shape must be [B, {T}, {C}, {H}, {W}], got {x.shape}")
        
        B = x.shape[0]
        
        # Process each t through encoder
        bots = []
        skips_t = {1: [], 2: [], 3: [], 4: []}
        
        for t in range(T):
            bot, s1, s2, s3, s4 = self.encoder(x[:, t])
            bots.append(bot)
            skips_t[1].append(s1)
            skips_t[2].append(s2)
            skips_t[3].append(s3)
            skips_t[4].append(s4)
            
        # ConvLSTM
        lstm_out = []
        h = torch.zeros(B, 256, 8, 8, device=x.device, dtype=x.dtype)
        c = torch.zeros(B, 256, 8, 8, device=x.device, dtype=x.dtype)
        for t in range(T):
            h, c = self.lstm(bots[t], (h, c))
            lstm_out.append(h)
            
        h_seq = torch.stack(lstm_out, dim=1) # [B, T, 256, 8, 8]
        
        # Temporal Attention
        a_seq = self.attn(h_seq)
        
        # Decoder
        yb_out = []
        ye_out = []
        for t in range(T):
            skips = (skips_t[1][t], skips_t[2][t], skips_t[3][t], skips_t[4][t])
            d = self.decoder(a_seq[:, t], skips)
            
            yb = torch.sigmoid(self.head_bust(d))
            ye = F.softplus(self.head_error(d))
            
            yb_out.append(yb)
            ye_out.append(ye)
            
        Yb = torch.stack(yb_out, dim=1)
        Ye = torch.stack(ye_out, dim=1)
        
        return {"bust": Yb, "error": Ye}
