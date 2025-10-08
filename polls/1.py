import torch
import os

os.environ['CUDA_VISIBLE_DEVICES'] = '6'
device = torch.device('cuda:0')

try:
    x = torch.randn(1024, 1024, 1024, device=device)
    print("Success! GPU 6 is usable.")
except RuntimeError as e:
    print("CUDA error:", e)
