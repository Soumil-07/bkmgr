from pathlib import Path

import toml

STUB_CONFIG = """
[email]
smtp     = \"Your email provider's SMTP host\"
port     = 587 # Usually the default port
username = \"Username: Usually your email address\"
password = \"Password or App Password\"
from     = \"Usually same as your username\"
to       = \"Your e-book reader's email address\"
"""

config = None


def get_config():
    global config
    if config is not None:
        return config
    config_path = Path.home() / '.bkmgr' / 'config.toml'

    if not config_path.exists():
        print("Could not find config at \"{}\". \
            Creating a skeleton config file.".format(config_path.absolute()))
        config_path.write_text(STUB_CONFIG)
        return

    config = toml.load(config_path)
    return config
