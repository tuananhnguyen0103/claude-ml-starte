"""Đọc config YAML và áp dụng override dạng key=value từ dòng lệnh."""
import copy

import yaml


def load_config(path, overrides=None):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg = copy.deepcopy(cfg)
    for item in overrides or []:
        key, _, raw = item.partition("=")
        if not key or not _:
            raise ValueError(f"Override phải có dạng key=value, nhận được: {item!r}")
        node = cfg
        parts = key.split(".")                      # hỗ trợ key lồng nhau: model.width=64
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = yaml.safe_load(raw)       # "0.01" → float, "true" → bool, "sgd" → str
    return cfg
