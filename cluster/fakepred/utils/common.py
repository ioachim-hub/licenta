import argparse
import pathlib
import os


def get_settings_path(file_path: str = None) -> pathlib.Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--settings_path", type=str, help="Settings file", required=False, default=None
    )
    args, _ = parser.parse_known_args()

    settings_path_str: str
    if file_path:
        settings_path_str = file_path
    elif args.settings_path:
        settings_path_str = args.settings_path
    elif os.getenv("SETTINGS_PATH"):
        env_var = os.getenv("SETTINGS_PATH")
        if env_var:
            settings_path_str = env_var
    else:
        raise RuntimeError("settings_path/SETTINGS_PATH not specified")

    settings_path = pathlib.Path(settings_path_str)

    if not settings_path.exists():
        raise RuntimeError(f"settings_path ({settings_path}) does not exist")

    return settings_path
