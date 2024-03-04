import toml
from kube_dashboard import KubeDashboard
import argparse
import os
import logging
from prettytable import PrettyTable

CONFIG_FILE = 'config.toml'


def get_log(name='KC', save_logs=False, log_file='kc.log', log_level='INFO'):
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(log_level)
    if save_logs:
        logger.addHandler(logging.FileHandler(log_file))
    return logger


def get_parser():
    parser = argparse.ArgumentParser(
        description='Tool to work with kubernetes dashboard, if there is no kubectl access.'
                    f'For the first run config file {CONFIG_FILE} is creates within the same folder.'
                    'Open the config file and fill in kubernetes dashboard URL and access token.'
                    'There can be many clusters defined in the config file, but only one can be operated at once.')
    parser.add_argument('-u', '--clusters', help='list cluster names from the config file', action='store_true')
    parser.add_argument('-n', '--namespace', help='set the default namespace to work with', type=str)
    parser.add_argument('-c', '--cluster', help='set the default cluster to work with', type=str)

    parser.add_argument('-d', '--deploy', help='list deployment names', action='store_true')
    parser.add_argument('-p', '--pods', help='list pods', action='store_true')
    parser.add_argument('-j', '--jobs', help='list jobs', action='store_true')

    parser.add_argument('-l', '--logs', help='tail pods logs by name patterns separated by spaces.\n'
                                             '⚠️ the tool works via http. Do not set too much at once!\n'
                                             'Example 1: kc -l nginx -> will get all pods with name nginx\n'
                                             'Example 2: kc -l nginx hello -> will get all pods with name nginx and hello\n'
                                             'Example 3: kc -l hello-6779dffb89-m6bc9 -> will get logs from specific pod',
                        nargs='+')
    parser.add_argument('-jl', '--joblog', help='tail the log of the latest job with matching pattern', nargs=1)
    parser.add_argument('-s', '--scale', help='scale deployment by name pattern', nargs=2,
                        metavar=('pattern', 'replicas'))
    parser.add_argument('-x', '--delete', help='delete the 1st pod by matching pattern', nargs=1)
    return parser


def create_config():
    default_config = {
        'default': {
            'cluster': 'localhost',
            'namespace': 'default'
        },
        'log': {
            'level': 'INFO',
            'file': 'kc.log',
            'save': False
        },
        'connection': {
            'retries': 3,
            'delay': 1
        },
        'cluster': {
            'default': {
                'url': 'http://localhost:8001',
                'token': 'secure 1'
            },
            'dev': {
                'url': 'https://k8s-dev.example.com',
                'token': 'secure 2'
            }
        }
    }
    save_config(default_config, CONFIG_FILE)


def save_config(cfg, file_path):
    with open(file_path, 'w') as file:
        toml.dump(cfg, file)


def read_config(file_path):
    with open(file_path, 'r') as file:
        cfg = toml.load(file)
    return cfg


def get_cluster_config(cfg):
    default = cfg['default']['cluster']
    cluster = cfg['cluster'][default].copy()
    cluster['name'] = default
    cluster.update(cfg['connection'])
    return cluster


def main():
    config = None

    if not os.path.isfile(CONFIG_FILE):
        create_config()
        print('Tool to work with kubernetes dashboard, if there is no kubectl access.\n'
              'For the first run config file config.toml is creates within the same folder.\n'
              'Open the config file and fill in kubernetes dashboard URL and access token.\n'
              'There can be many clusters defined in the config file, but only one can be operated at once.\n')
        exit(0)

    try:
        config = read_config(CONFIG_FILE)
    except Exception as e:
        print('Failed to read config file:', e)
        exit(1)
    log = get_log('KC',
                  save_logs=config['log']['save'],
                  log_file=config['log']['file'],
                  log_level=config['log']['level'])
    try:
        cluster_config = get_cluster_config(config)
    except Exception as e:
        log.error('Failed to get cluster config:', e)
        exit(1)

    dashboard = KubeDashboard(**cluster_config)

    parser = get_parser()
    args = parser.parse_args()

    if args.clusters:
        prettytable = PrettyTable()
        prettytable.field_names = ['Cluster', 'URL']
        for cluster, data in config['cluster'].items():
            prettytable.add_row([cluster, data['url']])
        print(prettytable)
        exit(0)

    if args.namespace:
        config['default']['namespace'] = args.namespace
        save_config(config, CONFIG_FILE)
        log.info(f'Namespace set to {args.namespace}')
        exit(0)

    if args.cluster:
        if args.cluster in config['cluster'].keys():
            config['default']['cluster'] = args.cluster
            save_config(config, CONFIG_FILE)
            log.info(f'Cluster set to {args.cluster}')
        else:
            log.error(f'Cluster {args.cluster} not found in the config file. Configure the cluster first.')
        exit(0)

    # actions with the dashboard ⬇️⬇️⬇️
    dashboard.authorize()

    if args.deploy:
        deployments = dashboard.get_deployments()
        table = PrettyTable()
        table.field_names = ['Name', 'Created', 'Desired Pods', 'Running Pods']
        table.add_rows([[d['name'], d['created'], d['desired_pods'], d['running_pods']] for d in deployments])
        print(table)
        exit(0)

    if args.pods:
        pods = dashboard.get_pods()
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


if __name__ == '__main__':
    main()
