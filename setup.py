import os
import shutil
import site
import subprocess
from pathlib import Path


def root_dir():
    return Path(__file__).resolve().parent


def sp_dir():
    sp_dir = os.environ.get("SP_DIR")
    if sp_dir:
        return Path(sp_dir)

    for path in site.getsitepackages():
        return Path(path)

    raise RuntimeError("Cannot determine site-packages directory")


def build_dir():
    return Path(os.environ.get("PYDIS_BUILD_DIR", root_dir() / "build")).resolve()


def build_type():
    return os.environ.get("CMAKE_BUILD_TYPE", "Release")


def default_compilers():
    cc = os.environ.get("CC")
    cxx = os.environ.get("CXX")
    if cc or cxx:
        return cc, cxx

    gcc14 = Path("/usr/bin/gcc-14")
    gpp14 = Path("/usr/bin/g++-14")
    if gcc14.exists() and gpp14.exists():
        return str(gcc14), str(gpp14)

    return None, None


def run(cmd):
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=root_dir())


def configure_cmake(build_path):
    cc, cxx = default_compilers()
    cmd = [
        "cmake",
        "-S",
        str(root_dir()),
        "-B",
        str(build_path),
        f"-DCMAKE_BUILD_TYPE={build_type()}",
    ]
    if cc:
        cmd.append(f"-DCMAKE_C_COMPILER={cc}")
    if cxx:
        cmd.append(f"-DCMAKE_CXX_COMPILER={cxx}")
    run(cmd)


def build_cmake(build_path):
    cmd = ["cmake", "--build", str(build_path)]
    parallel = os.environ.get("CMAKE_BUILD_PARALLEL_LEVEL")
    if parallel:
        cmd.extend(["-j", parallel])
    elif os.cpu_count():
        cmd.extend(["-j", str(os.cpu_count())])
    run(cmd)


def install_cmake(build_path):
    run(["cmake", "--install", str(build_path)])


def cmake_cache_value(build_path, key):
    cache = build_path / "CMakeCache.txt"
    if not cache.exists():
        raise FileNotFoundError(f"Missing CMake cache: {cache}")

    prefix = f"{key}:"
    for line in cache.read_text().splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1]

    raise KeyError(f"{key} not found in {cache}")


def installed_pydis_lib_dir(build_path):
    install_prefix = Path(cmake_cache_value(build_path, "CMAKE_INSTALL_PREFIX"))
    pydis_lib_dir = install_prefix / "pydis_lib"
    if not (pydis_lib_dir / "pydis_lib.py").exists():
        raise FileNotFoundError(f"Missing generated wrapper: {pydis_lib_dir / 'pydis_lib.py'}")
    if not (pydis_lib_dir / "libpydis.so").exists():
        raise FileNotFoundError(f"Missing shared library: {pydis_lib_dir / 'libpydis.so'}")
    return pydis_lib_dir


def install_pydis_lib(build_path):
    pkg_dir = sp_dir() / "pydis_lib"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    pydis_lib_dir = installed_pydis_lib_dir(build_path)
    shutil.copy2(pydis_lib_dir / "pydis_lib.py", pkg_dir / "__init__.py")
    shutil.copy2(pydis_lib_dir / "libpydis.so", pkg_dir / "libpydis.so")

    print(f"[pydis_lib] installed to {pkg_dir}")


def install_pydis():
    pkg_dir = sp_dir() / "pydis"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root_dir() / "pydis", pkg_dir, dirs_exist_ok=True)
    print(f"[pydis] installed to {pkg_dir}")


def main():
    build_path = build_dir()
    configure_cmake(build_path)
    build_cmake(build_path)
    install_cmake(build_path)
    install_pydis_lib(build_path)
    install_pydis()


if __name__ == "__main__":
    main()
