import os
import shutil
import tempfile
import subprocess


def clone_github_repo(repo_url, local_base="D:/temp_repos"):
    os.makedirs(local_base, exist_ok=True)
    temp_dir = tempfile.mkdtemp(dir=local_base)
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        print(f"Repo cloned to: {temp_dir}")
        return temp_dir
    except subprocess.CalledProcessError as e:
        print("Error while cloning repo:", e)
        shutil.rmtree(temp_dir)
        return None
