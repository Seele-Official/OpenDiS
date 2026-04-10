import importlib.util


def show_spec(name: str) -> None:
    spec = importlib.util.find_spec(name)
    if spec is None or spec.origin is None:
        raise ModuleNotFoundError(name)
    print(f"{name}: {spec.origin}")


show_spec("pydis")
show_spec("pydis_lib")
