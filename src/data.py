"""Dataset CIFAR-10 (train thật) hoặc FakeData (smoke test: không cần mạng, chạy vài giây trên CPU)."""
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

MEAN = (0.4914, 0.4822, 0.4465)
STD = (0.2470, 0.2435, 0.2616)


def _transforms(augment):
    norm = [transforms.ToTensor(), transforms.Normalize(MEAN, STD)]
    aug = [transforms.RandomCrop(32, padding=4), transforms.RandomHorizontalFlip()] if augment else []
    return transforms.Compose(aug + norm), transforms.Compose(norm)


def build_datasets(cfg, data_dir, smoke):
    train_tf, val_tf = _transforms(cfg["data"].get("augment", True))
    if smoke:
        n = cfg["data"].get("smoke_size", 64)
        train = datasets.FakeData(size=n, image_size=(3, 32, 32), num_classes=10, transform=train_tf)
        val = datasets.FakeData(size=n // 2, image_size=(3, 32, 32), num_classes=10, transform=val_tf, random_offset=n)
        return train, val
    train = datasets.CIFAR10(data_dir, train=True, download=True, transform=train_tf)
    val = datasets.CIFAR10(data_dir, train=False, download=True, transform=val_tf)
    return train, val


def make_train_loader(dataset, cfg, epoch, skip_batches=0, num_workers=0):
    """Thứ tự batch của mỗi epoch cố định theo (seed, epoch), nên resume giữa epoch chỉ cần bỏ qua các batch đã train."""
    bs = cfg["train"]["batch_size"]
    g = torch.Generator().manual_seed(cfg["seed"] + epoch)
    order = torch.randperm(len(dataset), generator=g).tolist()
    order = order[: (len(order) // bs) * bs]          # bỏ batch lẻ: mọi epoch có cùng số batch
    # generator riêng: nếu không, mỗi lần tạo iterator DataLoader rút seed từ RNG toàn cục,
    # phiên resume sẽ rút thêm một lần và augmentation/dropout lệch so với chạy một mạch
    return DataLoader(dataset, batch_size=bs, sampler=order[skip_batches * bs:], drop_last=True, generator=g,
                      num_workers=num_workers, pin_memory=torch.cuda.is_available())


def make_val_loader(dataset, cfg, num_workers=0):
    return DataLoader(dataset, batch_size=cfg["train"]["batch_size"] * 2, shuffle=False,
                      generator=torch.Generator().manual_seed(cfg["seed"]),
                      num_workers=num_workers, pin_memory=torch.cuda.is_available())
