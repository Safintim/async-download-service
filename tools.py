import os
import argparse
import pathlib
import yaml

BASE_DIR = pathlib.Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'conf.yaml'


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--FILES_DIR', type=is_exists_dir)
    parser.add_argument('-dl', '--RESPONSE_DELAY')
    parser.add_argument('-n', '--ARCHIVE_NAME')
    parser.add_argument('-l', '--LOGGING', action='store_true', default=False)
    return parser


def is_exists_dir(dirpath):
    if os.path.exists(dirpath):
        return dirpath
    raise argparse.ArgumentTypeError('dir not found')


def get_config_from_file(path=CONFIG_PATH):
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


def setup_config(config_from_cli):
    config_from_file = get_config_from_file()

    for key, value in config_from_cli.items():
        if value:
            config_from_file[key] = value
    return config_from_file
