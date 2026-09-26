"""Nhận diện môi trường chạy (local / colab / kaggle) và đường dẫn mặc định."""
import os

DEFAULT_PATHS = {
    "colab":  {"data": "/content/data", "ckpt": "/content/drive/MyDrive/ckpt"},
    "kaggle": {"data": "/tmp/data",     "ckpt": "/kaggle/working/ckpt"},
    "local":  {"data": "./data",        "ckpt": "./checkpoints"},
}


def detect_env():
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
        return "kaggle"
    if "COLAB_RELEASE_TAG" in os.environ or "COLAB_GPU" in os.environ:
        return "colab"
    return "local"


def default_path(kind):
    return DEFAULT_PATHS[detect_env()][kind]
