import toml
import argparse
import os
import logging
import pyperclip
from prettytable import PrettyTable
from kdc.kube_dashboard import KubeDashboard

CONFIG_FILE_NAME = 'config.toml'
CONFIG_FILE_FOLDER = '.kdc'
CONFIG_FILE_PATH = CONFIG_FILE_FOLDER + '/' + CONFIG_FILE_NAME


def get_log(name='KDC', save_logs=False, log_file='kdc.log', log_level='INFO'):
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(log_level)
    if save_logs:
        logger.addHandler(logging.FileHandler(log_file))
    return logger


def get_parser():
    parser = argparse.ArgumentParser(
        description='Tool to work with kubernetes dashboard, if there is no kubectl access.'
                    f'For the first run file ~/{CONFIG_FILE_PATH} is created'
                    'Open the config file and fill in kubernetes dashboard URL and access token.'
                    'There can be many clusters defined in the config file, but only one can be operated at once.')
    parser.add_argument('-e', '--envs', help='list cluster (evn) names from the config file', action='store_true')
    parser.add_argument('-n', '--namespace', help='set the default namespace to work with', type=str)
    parser.add_argument('-c', '--cluster', help='set the default cluster to work with', type=str)
    parser.add_argument('-t', '--token', help='show and copy to clipboard the token of selected cluster',
                        action='store_true')

    parser.add_argument('-d', '--deploy', help='list deployment names', action='store_true')
    parser.add_argument('-p', '--pods', help='list pods. Use n=name to filter by name, s=status to filter by status',
                        nargs='*')
    parser.add_argument('-j', '--jobs', help='list jobs', action='store_true')

    parser.add_argument('-l', '--logs', help='tail pods logs by name patterns separated by spaces.\n'
                                             '⚠️ the tool works via http. Do not set too much at once!\n'
                                             'Example 1: kdc -l nginx -> will get all pods with name nginx\n'
                                             'Example 2: kdc -l nginx hello -> will get all pods with name nginx and hello\n'
                                             'Example 3: kdc -l hello-6779dffb89-m6bc9 -> will get logs from specific pod',
                        nargs='+')
    parser.add_argument('-jl', '--joblog', help='tail the log of the latest job with matching pattern', type=str)
    parser.add_argument('-s', '--scale', help='scale deployment by name pattern', nargs=2,
                        metavar=('pattern', 'replicas'))
    parser.add_argument('-x', '--delete', help='delete the 1st pod by matching pattern', type=str)
    parser.add_argument('-w', '--whereisconfig', help='show where the config file is located', action='store_true')
    parser.add_argument('-f', '--file', help='download and save selected pod logs', nargs='+')
    return parser


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
                'token': 'secure 1'
            },
            'dev': {
                'url': 'https://k8s-dev.example.com',
                'token': 'secure 2'
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


def app():
    try:
        config = get_config(CONFIG_FILE_PATH)
    except Exception:
        print('Failed to read config file:')
        exit(1)
    log = get_log(save_logs=config['log']['save'],
                  log_file=config['log']['file'],
                  log_level=config['log']['level'])
    try:
        cluster_config = get_cluster_config(config)
        if not cluster_config:
            log.error('There is no clusters in the config')
            exit(1)
    except Exception:
        log.error('Failed to get cluster config')
        exit(1)

    parser = get_parser()
    args = parser.parse_args()

    dashboard = KubeDashboard(**cluster_config)

    if args.envs:
        prettytable = PrettyTable()
        prettytable.field_names = ['Cluster', 'URL']
        for cluster, data in config['cluster'].items():
            prettytable.add_row([cluster, data['url']])
        print(prettytable)
        exit(0)

    if args.namespace:
        config['default']['namespace'] = args.namespace
        save_config(config, CONFIG_FILE_PATH)
        log.info(f'Namespace set to {args.namespace}')
        exit(0)

    if args.cluster:
        if args.cluster in config['cluster'].keys():
            config['default']['cluster'] = args.cluster
            save_config(config, CONFIG_FILE_PATH)
            log.info(f'Cluster set to {args.cluster}')
        else:
            log.error(f'Cluster {args.cluster} not found in the config file. Configure the cluster first.')
        exit(0)

    if args.token:
        default_cluster = config['default']['cluster']
        cluster = config['cluster'].get(default_cluster)
        pyperclip.copy(cluster['token'])
        log.warning(f'Cluster {default_cluster} token. ⚠️Copied to clipboard ⚠️\n\n{cluster["token"]} \n')
        exit(0)

    if args.whereisconfig:
        home_dir = os.path.expanduser('~')
        file_path = os.path.join(home_dir, CONFIG_FILE_PATH)
        log.info(f'Config file location:\n\n{file_path}\n')
        exit(0)

    # actions with the dashboard ⬇️⬇️⬇️

    if args.deploy:
        deployments = dashboard.get_deployments()
        table = PrettyTable()
        table.field_names = ['Name', 'Created', 'Desired Pods', 'Running Pods']
        table.add_rows([[d['name'], d['created'], d['desired_pods'], d['running_pods']] for d in deployments])
        print(table)
        exit(0)

    if args.pods is not None:
        pod_filter = dict()
        for arg in args.pods:
            if arg.startswith('n='):
                pod_filter['name_filter'] = arg[2:]
            if arg.startswith('s='):
                pod_filter['status_filter'] = arg[2:]
        pods = dashboard.get_pods(**pod_filter)
        table = PrettyTable()
        table.field_names = ['App', 'Name', 'Restarts', 'Status', 'Created']
        table.add_rows([[p['appLabel'], p['name'], p['restarts'], p['status'], p['created']] for p in pods])
        print(table)
        exit(0)

    if args.jobs:
        jobs = dashboard.get_jobs()
        table = PrettyTable()
        table.field_names = ['Name', 'Status', 'Created']
        table.add_rows([[j['name'], j['status'], j['created']] for j in jobs])
        print(table)
        exit(0)

    if args.logs:
        dashboard.tail_pods_logs(*args.logs)
        exit(0)

    if args.joblog:
        dashboard.tail_latest_job_logs(args.joblog)
        exit(0)

    if args.scale:
        dashboard.scale_deploy(args.scale[0], int(args.scale[1]))
        exit(0)

    if args.delete:
        dashboard.delete_pods(args.delete[0])
        exit(0)

    if args.file:
        dashboard.save_logs(*args.file)
        exit(0)

    print('No action specified. Use -h to see the help.')


def main():
    try:
        app()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        exit(0)


if __name__ == '__main__':
    main()
