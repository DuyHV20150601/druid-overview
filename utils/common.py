import os
import yaml
from pathlib import Path
from datetime import datetime

ENV = os.environ.get("ENV")
if ENV == "dev":
    CONFIG_PATH = "config/dev"
elif ENV == "prod":
    CONFIG_PATH = "config/prod"
else:
    raise Exception("ENV is not found!!!!")


def get_config(config_file):
    path = Path(CONFIG_PATH) / config_file
    with open(path, "r") as fpt:
        return yaml.safe_load(fpt)


def date_str_no_dash(date: datetime):
    return date.strftime("%Y%m%d")


def date_str_dash(date: datetime):
    return date.strftime("%Y-%m-%d")
