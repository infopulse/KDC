import os
import toml
import subprocess
import logging


def get_log(name='KDC', save_logs=False, log_file='kdc.log', log_level='INFO'):
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(log_level)
    if save_logs:
        logger.addHandler(logging.FileHandler(log_file))
    return logger


def open_config_file(filename: str):
    if os.name == 'nt':  # For Windows
        os.startfile(filename)
    elif os.name == 'posix':  # For Linux, Mac
        subprocess.call(('xdg-open', filename))


def create_config(file_name: str) -> dict:
    default_config = {
        'default': {
            'cluster': 'localhost',
            'namespace': 'default'
        },
        'log': {
            'level': 'INFO',
            'file': 'kdc.log',
            'save': False
        },
        'connection': {
            'retries': 3,
            'delay': 1
        },
        'cluster': {
            'localhost': {
                'url': 'http://localhost:8001',
                'token': 'secure 1',
            },
            'dev': {
                'url': 'https://k8s-dev.example.com',
                'token': 'secure 2',
            }
        }
    }
    save_config(default_config, file_name)
    return default_config


def get_config(file_name: str) -> dict:
    home_dir = os.path.expanduser('~')
    file_path = os.path.join(home_dir, file_name)
    if not os.path.isfile(file_path):
        return create_config(file_path)
    else:
        return read_config(file_path)


def save_config(cfg: dict, file_name: str) -> None:
    home_dir = os.path.expanduser('~')
    file_path = os.path.join(home_dir, file_name)
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, 'w') as file:
        toml.dump(cfg, file)


def read_config(file_path):
    with open(file_path, 'r') as file:
        cfg = toml.load(file)
    return cfg


def get_cluster_config(cfg: dict) -> dict or None:
    default = cfg['default']['cluster']
    cluster = cfg['cluster'].get(default)
    if len(cfg['cluster']) == 0:
        return None
    if not cluster:
        default = tuple(cfg['cluster'].keys())[0]
        cluster = cfg['cluster'].get(default)
    cluster['name'] = default
    cluster.update(cfg['connection'])
    return cluster


def get_version_from_pyproject():
    data = toml.load("pyproject.toml")
    version = data['project']['version']
    return version
