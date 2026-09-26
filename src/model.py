"""Các model cho CIFAR-10 (ảnh 32x32, 10 lớp)."""
import torch.nn as nn
from torchvision.models import resnet18


def _block(cin, cout):
    return nn.Sequential(
        nn.Conv2d(cin, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
        nn.Conv2d(cout, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


class SmallCNN(nn.Module):
    """3 khối conv (32→16→8→4), đủ nhỏ để train nhanh trên GPU T4 miễn phí."""

    def __init__(self, num_classes=10, width=32, dropout=0.2):
        super().__init__()
        self.features = nn.Sequential(_block(3, width), _block(width, 2 * width), _block(2 * width, 4 * width))
        self.head = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(dropout),
                                  nn.Linear(4 * width, num_classes))

    def forward(self, x):
        return self.head(self.features(x))


def _resnet18_cifar(num_classes):
    m = resnet18(num_classes=num_classes)
    m.conv1 = nn.Conv2d(3, 64, 3, stride=1, padding=1, bias=False)   # ảnh 32x32: bỏ stride 2 ở lớp đầu
    m.maxpool = nn.Identity()
    return m


def build_model(cfg):
    mc = cfg["model"]
    if mc["name"] == "small_cnn":
        return SmallCNN(mc.get("num_classes", 10), mc.get("width", 32), mc.get("dropout", 0.2))
    if mc["name"] == "resnet18":
        return _resnet18_cifar(mc.get("num_classes", 10))
    raise ValueError(f"Model không hỗ trợ: {mc['name']!r} (có: small_cnn, resnet18)")
