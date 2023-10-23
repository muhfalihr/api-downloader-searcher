import os
import logging.config
from configparser import ConfigParser

import yaml


def setup_logging(
    default_path="logging.yaml",
    default_level=logging.INFO,
    env_key="LOG_CFG",
    log_section=None,
):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    configparser = ConfigParser()
    configparser.read("config.ini")
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt") as f:
            config = yaml.safe_load(f.read())
            if log_section:
                if configparser.getboolean("log", "sectionable"):
                    filepath = os.path.join(
                        configparser.get("log", "path"), log_section
                    )
                else:
                    filepath = os.path.join(configparser.get("log", "path"))
                if not os.path.exists(filepath):
                    os.makedirs(filepath)
                info_file_name = "%s/%s" % (
                    filepath,
                    config["handlers"]["info_file_handler"]["filename"],
                )
                error_file_name = "%s/%s" % (
                    filepath,
                    config["handlers"]["error_file_handler"]["filename"],
                )
                debug_file_name = "%s/%s" % (
                    filepath,
                    config["handlers"]["debug_file_handler"]["filename"],
                )

                config.get("handlers", {}).get("info_file_handler", {})[
                    "filename"
                ] = info_file_name
                config.get("handlers", {}).get("error_file_handler", {})[
                    "filename"
                ] = error_file_name
                config.get("handlers", {}).get("debug_file_handler", {})[
                    "filename"
                ] = debug_file_name

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
