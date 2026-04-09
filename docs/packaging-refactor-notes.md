# Packaging Refactor Notes

This note records the local packaging and layout refactor that was added on top of upstream in the two commits below:

- `9a1190d` (`2025-12-23 00:29 +0800`) `conda package`
- `00927c3` (`2025-12-23 00:35 +0800`) `conda package`

The second commit mostly reverted part of the first rename so that the C sources stayed under `core/pydis/` while the packaging entry points introduced in the first commit remained in place.

## What Changed

The refactor had two main goals:

- make the Python package importable from a top-level `pydis/` package
- provide a simple local install and conda packaging path for `pydis` and the generated `pydis_lib` shared library

### Python Package Layout

Before the refactor, the Python sources were spread across:

- `core/pydis/python/pydis/`
- `python/framework/`

The refactor moved or copied those pieces into a top-level package tree:

- `pydis/`
- `pydis/calforce/`
- `pydis/collision/`
- `pydis/framework/`
- `pydis/mobility/`
- `pydis/nbrlist/`
- `pydis/remesh/`
- `pydis/simulate/`
- `pydis/timeint/`
- `pydis/topology/`
- `pydis/util/`
- `pydis/visualize/`

This is why example code can now import directly with:

```python
from pydis.framework.disnet_manager import DisNetManager
```

instead of manually editing `sys.path`.

### Packaging Entry Points

Two packaging files were added at the repository root:

- [setup.py](/home/seele/OpenDiS/setup.py)
- [meta.yaml](/home/seele/OpenDiS/meta.yaml)

`setup.py` is not a normal setuptools build. It is a local packaging entry point that:

1. chooses a CMake build directory from `PYDIS_BUILD_DIR`, defaulting to `build/`
2. configures CMake for that build directory
3. builds the native targets
4. runs `cmake --install` for that build directory
5. reads `CMAKE_INSTALL_PREFIX` from the build directory's `CMakeCache.txt`
6. copies `<install-prefix>/pydis_lib/pydis_lib.py` to `site-packages/pydis_lib/__init__.py`
7. copies `<install-prefix>/pydis_lib/libpydis.so` to `site-packages/pydis_lib/libpydis.so`
8. copies the repository `pydis/` tree to `site-packages/pydis/`

It defaults to `gcc-14/g++-14` when they are available locally and `CC`/`CXX` are not already set.

`meta.yaml` wraps the same entry point, so the CMake build is now driven from the packaging step itself.

### CMake Structure

The first refactor commit temporarily renamed the C sources from `core/pydis/` to `core/pydis_lib/`.
The follow-up commit `00927c3` moved them back to `core/pydis/`.

Current state:

- the source tree remains under `core/pydis/`
- top-level [CMakeLists.txt](/home/seele/OpenDiS/CMakeLists.txt) still builds `core/pydis`
- the default install output lands under the chosen build directory, for example `build/install/pydis_lib/`

That means the naming split is intentional:

- source module name: `core/pydis`
- installed binary Python wrapper package: `pydis_lib`
- installed pure Python package: `pydis`

### Other Effects From The Original Refactor

The first commit also:

- removed several old extension/lib placeholder directories
- deleted some old `tests/test1_node_force` and `tests/test2_topol_op` files from the packaged branch
- added `pydis/graph/` as a tracked directory instead of the old nested submodule path

## Necessary Local Adjustments Still Worth Keeping

The only uncommitted change in the examples that clearly matches the refactor is:

- [examples/01_loop/test_disl_loop_pydis.py](/home/seele/OpenDiS/examples/01_loop/test_disl_loop_pydis.py)

That file was updated to import from `pydis.framework...` directly instead of pushing local source directories into `sys.path`.

That change is consistent with the packaging refactor and should be kept.

## Current Packaging Flow

The current packaging flow is a single local entry point driven by `setup.py`.

### 1. Install Into A Python Environment

To install into a specific Python environment, point `SP_DIR` at its `site-packages`:

```bash
SP_DIR=$CONDA_PREFIX/lib/python3.13/site-packages python setup.py
```

By default, `setup.py` will:

- use `build/` as the CMake build directory
- configure CMake with `Release`
- prefer `gcc-14/g++-14` if `CC` and `CXX` are not set
- build, install, and then copy the Python package files

To use a different build directory:

```bash
PYDIS_BUILD_DIR=build-gcc14 SP_DIR=$CONDA_PREFIX/lib/python3.13/site-packages python setup.py
```

If `SP_DIR` is not set, `setup.py` uses Python's default `site.getsitepackages()`.

### 2. Build A Conda Package

If using conda-build:

```bash
conda build .
```

This still targets local packaging, but it no longer assumes a manual CMake step happened earlier.

## Practical Interpretation

The refactor still does not convert the project into a standard Python package build.
It keeps a local packaging layer on top of the existing CMake build:

- `setup.py` drives CMake configure/build/install for a selected build directory
- `setup.py` reads the install prefix from that concrete build directory
- `setup.py` copies those installed files into Python's package directory
- `meta.yaml` delegates to `setup.py`

So when updating from upstream, the key thing to preserve is not a complicated build backend.
It is this contract:

- keep the top-level `pydis/` package layout
- keep `setup.py`
- keep `meta.yaml`
- keep the assumption that packaging is driven from a concrete CMake build directory and its install prefix
