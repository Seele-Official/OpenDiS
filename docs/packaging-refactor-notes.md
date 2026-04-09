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

`setup.py` is not a normal setuptools build. It is a small installer script that:

1. finds a target `site-packages` directory, optionally using `SP_DIR`
2. copies `build/install/pydis_lib/pydis_lib.py` to `site-packages/pydis_lib/__init__.py`
3. copies `build/install/pydis_lib/libpydis.so` to `site-packages/pydis_lib/libpydis.so`
4. copies the repository `pydis/` tree to `site-packages/pydis/`

`meta.yaml` wraps that installer for conda, but it assumes the C/C++ build products already exist in `build/install/`.

### CMake Structure

The first refactor commit temporarily renamed the C sources from `core/pydis/` to `core/pydis_lib/`.
The follow-up commit `00927c3` moved them back to `core/pydis/`.

Current state:

- the source tree remains under `core/pydis/`
- top-level [CMakeLists.txt](/home/seele/OpenDiS/CMakeLists.txt) still builds `core/pydis`
- the install output lands in `build/install/pydis_lib/`

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

The current packaging flow is a two-stage process.

### 1. Build Native Artifacts

Configure and build:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
cmake --install build
```

After this, the key artifacts should exist:

- `build/install/pydis_lib/pydis_lib.py`
- `build/install/pydis_lib/libpydis.so`

### 2. Install or Package Python Pieces

To install into a specific Python environment, point `SP_DIR` at its `site-packages`:

```bash
SP_DIR=$CONDA_PREFIX/lib/python3.13/site-packages python setup.py
```

If `SP_DIR` is not set, `setup.py` uses Python's default `site.getsitepackages()`.

### 3. Build A Conda Package

If using conda-build:

```bash
conda build .
```

Important caveat: the current [meta.yaml](/home/seele/OpenDiS/meta.yaml) does not build the native library itself.
It expects the native artifacts from the CMake step to already exist under `build/install/`.

## Practical Interpretation

The refactor did not convert the project into a self-contained Python package build.
It added a local packaging layer on top of the existing CMake build:

- CMake builds native code and installs files into `build/install/`
- `setup.py` copies those installed files into Python's package directory
- `meta.yaml` delegates to `setup.py`

So when updating from upstream, the key thing to preserve is not a complicated build backend.
It is this contract:

- keep the top-level `pydis/` package layout
- keep `setup.py`
- keep `meta.yaml`
- keep the assumption that `build/install/pydis_lib/` is populated before packaging
