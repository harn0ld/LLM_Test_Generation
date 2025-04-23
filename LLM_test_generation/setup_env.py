import subprocess
import sys
import os


def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def download_spacy_model():
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])


def main():
    if not os.path.exists("requirements.txt"):
        print("Error. Cannot find file requirements.txt")
        return

    install_requirements()
    download_spacy_model()
    print("Successfully downloaded requirements")


if __name__ == "__main__":
    main()
