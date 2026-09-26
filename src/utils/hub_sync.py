"""(Tùy chọn) Đồng bộ checkpoint lên Hugging Face Hub (repo private) để resume chéo Colab ↔ Kaggle.

Cần biến môi trường HF_TOKEN. `huggingface_hub` có sẵn trên Colab và Kaggle nên không nằm trong requirements.txt.
"""
import os

_created = set()


def push(local_path, repo_id, run_name, name=None):
    from huggingface_hub import HfApi

    api = HfApi(token=os.environ["HF_TOKEN"])
    if repo_id not in _created:
        api.create_repo(repo_id, private=True, exist_ok=True)
        _created.add(repo_id)
    api.upload_file(path_or_fileobj=local_path, repo_id=repo_id,
                    path_in_repo=f"{run_name}/{name or os.path.basename(local_path)}")


def pull(repo_id, run_name, dest_dir):
    from huggingface_hub import hf_hub_download

    try:
        return hf_hub_download(repo_id=repo_id, filename=f"{run_name}/last.pt",
                               local_dir=os.path.join(dest_dir, "_hub"), token=os.environ["HF_TOKEN"])
    except Exception as e:
        print(f"[hub] chưa có checkpoint {run_name}/last.pt trên {repo_id} ({type(e).__name__}) → train từ đầu")
        return None
