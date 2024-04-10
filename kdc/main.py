import argparse
import os
import pyperclip
from prettytable import PrettyTable
from kdc.kube_dashboard import KubeDashboard
from kdc.config import (get_config, save_config, get_cluster_config,
                        open_config_file, get_log, get_version,
                        get_namespace, set_namespace)

CONFIG_FILE_NAME = 'config.toml'
CONFIG_FILE_FOLDER = '.kdc'
CONFIG_FILE_PATH = CONFIG_FILE_FOLDER + '/' + CONFIG_FILE_NAME


def get_parser():
    parser = argparse.ArgumentParser(
        description='Tool to work with kubernetes dashboard, if there is no kubectl access.'
                    f'For the first run file ~/{CONFIG_FILE_PATH} is created'
                    'Open the config file and fill in kubernetes dashboard URL and access token.'
                    'There can be many clusters defined in the config file, but only one can be operated at once.')
    parser.add_argument('-e', '--env', help='list or set cluster (evn) names from the config file',
                        nargs='?', type=str, const='!', default=None)
    parser.add_argument('-n', '--namespace', help='list namespaces or set the default namespace to work with',
                        type=str, nargs='?', const='!', default=None)
    # parser.add_argument('-c', '--cluster', help='set the default cluster to work with', type=str)
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
    parser.add_argument('-o', '--openconfig', help='open the config file in the default editor', action='store_true')
    parser.add_argument('-v', '--version', help='show the current version', action='store_true')
    return parser


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

    if args.version:
        version = get_version()
        print(f'kdc version: {version}')
        exit(0)

    dashboard = KubeDashboard(**cluster_config)

    if args.env == '!':
        prettytable = PrettyTable()
        prettytable.field_names = ['Selected', 'Cluster', 'URL']
        for cluster, data in config['cluster'].items():
            selected = '------>' if cluster == config['default']['cluster'] else ''
            prettytable.add_row([selected, cluster, data['url']])
        print(prettytable)
        exit(0)
    elif args.env is not None:
        config = get_config(CONFIG_FILE_PATH)
        if args.env in config['cluster'].keys():
            config['default']['cluster'] = args.env
            save_config(config, CONFIG_FILE_PATH)
            log.info(f'Cluster set to {args.env}')
        else:
            log.error(f'Cluster {args.env} not found in the config file. Configure the cluster first.')
        exit(0)

    if args.namespace == '!':
        config = get_config(CONFIG_FILE_PATH)
        prettytable = PrettyTable()
        prettytable.field_names = ['Selected', 'Name', 'Phase', 'UID']
        namespaces = dashboard.get_namespaces()
        for namespace in namespaces:
            selected = '------>' if namespace['name'] == get_namespace(config) else ''
            prettytable.add_row([selected, namespace['name'], namespace['phase'], namespace['uid']])
        print(prettytable)
        exit(0)
    elif args.namespace is not None:
        config = get_config(CONFIG_FILE_PATH)
        config = set_namespace(config, args.namespace)
        save_config(config, CONFIG_FILE_PATH)
        log.info(f'Namespace set to {args.namespace}')
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

    if args.openconfig:
        home_dir = os.path.expanduser('~')
        file_path = os.path.join(home_dir, CONFIG_FILE_PATH)
        try:
            open_config_file(file_path)
        except Exception:
            log.error(f'Failed to open the file {file_path} in the default editor. Try to open it manually.')
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

    if not args.namespace:
        print('No action specified. Use -h to see the help.')


def main():
    try:
        app()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        exit(0)


if __name__ == '__main__':
    main()
