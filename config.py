from pathlib import Path

import toml

config = None

def get_config():
    global config
    if config is not None:
        return config
    config_path = Path.home() / '.bkmgr' / 'config.toml'

    if not config_path.exists():
        print("Could not find config at \"{}\"".format(config_path.absolute()))
        return

    config = toml.load(config_path)
    return config
