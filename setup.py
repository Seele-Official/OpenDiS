import os
import sys
import shutil
from pathlib import Path
import site
import platform
import subprocess

def sp_dir():
    sp_dir = os.environ.get("SP_DIR")
    if sp_dir:
        return Path(sp_dir)


    for p in site.getsitepackages():
        return Path(p)

    raise RuntimeError("Cannot determine site-packages directory")

def root_dir():
    return Path(__file__).resolve().parent

def install_pydis_lib():
    pkg_dir = sp_dir() / "pydis_lib"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    pydis_lib_dir = root_dir() / "build/install/pydis_lib"

    shutil.copy2(pydis_lib_dir / "pydis_lib.py", pkg_dir / "__init__.py")
    shutil.copy2(pydis_lib_dir / "libpydis.so", pkg_dir / "libpydis.so")

    print(f"[pydis_lib] installed to {pkg_dir}")

def install_pydis():
    pkg_dir = sp_dir() / "pydis"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    pydis_dir = root_dir() / "pydis"
    
    shutil.copytree(pydis_dir, pkg_dir, dirs_exist_ok=True)


def main():
    install_pydis_lib()
    install_pydis()

if __name__ == "__main__":
    main()
