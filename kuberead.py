import requests as r
import argparse
import time
import json
from colorama import init, Fore, Back, Style
import datetime as dt
import sys
import urllib3

urllib3.disable_warnings()

KUBE = {'CERT': 'https://kube-dashboard.wsalesmdw.hcbe.cert.corp',
        # 'DEV': 'https://whs-dashboard:whs-d4shb04rd@kube-dashboard.wsalesmdw.hcbe.dev.corp',
        'DEV': 'https://kube-dashboard.wsalesmdw.hcbe.dev.corp',
        'DEVFRT': 'https://whs-dashboard:whs-d4shb04rd@kube-dashboard.wsalesfrt.hcbe.dev.corp',
        'CERTFRT': 'https://kube-dashboard.wsalesfrt.hcbe.dev.corp',
        'PRO': 'http://kube-dashboard.wsalesmdw.hcbe.corp'
        }

TOKEN = {
    'DEV': 'eyJhbGciOiJSUzI1NiIsImtpZCI6Ikw3UmQzLWtqTHBiN19wM0swZmJ3WUJrcVNPZVE2Rk5fcmQ0R3NDSjhSX3MifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZC10b2tlbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjViZjQ3ZDViLWY4NTYtNGZlMC05Yzc3LThiNTA3NGE5ZjgyOCIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlcm5ldGVzLWRhc2hib2FyZDprdWJlcm5ldGVzLWRhc2hib2FyZCJ9.UulTkwIBdatBIUoAhXICcYvefx87uB-2ZQyxS1kWVdk4UTh1oDvkGBRp2IraFhuN6FK3oajMLGfsotJwMbHaDcnypzB1ZhqITsUL-LXhgwH2mrN-IkR5pI7V9GWbrL9e9Xvcm_1Bm274S8FLlVKJMB5D1bS4ovp4VlEUWHHbP7EyZL7d5RHTm07hosMhrt6p8KYTPRIW9US5-hkKLFuJlbqBfthuZct7QiFHr2kIVCDZmOQ4rn0GwNVLmtKTFKg05KcmxHPQ_6aqS1KdnmquQwG3IeWuMy0YE0JxWTrdqcb0_cfGccunxnANmVST5OYcKO7zGkbQgOgOqR_SnE4qc-zYsi7kf5OynUDWl0ewFoPDdkB4TQUWtd-oQHCZisiD2M7xou_8QZ4RjQdwc01tB5PF8J97ZX4et6-rNB84c9fzgrVa35oBse1ACuc_XFg4IIA2-ByCiBVBQr_YVpwXN8Qi4YozlUREG_QaE_5Osa_Z5PjlrAYH643BgQGoX91-1PtuH4dh08o-iowPYcvEqIpiHXKrLbjO4a84Ekrg5nY8SXC1Kyh0vm0Bxz_fYdH_5Pts9Ey2G4-ZRpDDd00e-BksHTRU6BM_hLQ8f6gsEt7jisQ4Fs_rr5CsU2U4Kn05S0A0UAAz-9b-cJ_EtpBjh2ioRZfjt4jgxnXHMz8jxA4',
    'CERT': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImxlQ1doN2RUNjZYaHhNUkV0bC11RmVVTVpUaHg4RG1uVXNBYi1IZUhqSTgifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZC10b2tlbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjA4YWMxMzA1LTIwNjAtNGUzZC1hYjhhLTQyYmQ3NTk2NmQ4YiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlcm5ldGVzLWRhc2hib2FyZDprdWJlcm5ldGVzLWRhc2hib2FyZCJ9.SfaJPvbpbBYVUaRvYqUlie6MboYnY4K91Rd3UMfq5cwfPvEJU1HYAEjfy-VjltEN4XZ4UOA06z4HxfcuzEakYhQNNuQIlpgpmve7DqO_PTeR4O2cD6lYMzAJakFyeTLdp4JBv5kF_G5qpSmhqBNzVG6tXxu0p4Donddc7LhbLQ-Zf0DcsrgkwD8yNVnpuL7R7fLGg6dQjnVDEna9n3X27CVgt9h15HzrchllweD_oK5jpe0L3nWQmEfak4tEPKTeCBS63pnv6jf8tX9XhM2qBmumC169zyatmOzk-spOQc4pPovJk-bYdJTepaCOwQuPwqBTzCS39L03iRjqswMvYqf-OxZydQPr-7f_yqwPka-brxLS8nRHOY5GqYaBKtdizzREIoLMc3GrGRuprCo65gAddgzsDOCihNWHVtSE5aPH4pcmTPYmZpErstjOShBoCHeb6FQrlmkAnReDrzUiKmlYhIDIIX06HZ80wLq_7VJU2BRiDcYwzhKyfS-2hAF-60Ox3GzsJ-_lVX7lz9sMS-NHE7nPf9jL9vRN14Rmae3Q-ujMzrEslJK1XAyM0lXj4jRZ6yjf4j20suxCK58H7yp8PEoLaf6PXhjgHgkK8y5oSEwA-Juaqp9KMxbSeGCqkWP2vAct9BRyo_fH_pWEPCusOpsqO6wclcf4X1Mdi28',
    'PRO': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImFRWkJYSTVMWmpKekVGeVpNejZCVlFKNE8yOVVDWUtOQnJOODN5VDQtREEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZC10b2tlbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImM2YTcxMDlhLTRmOWUtNGE3OS05NTkyLTk5OWU5MGM0YjYzYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlcm5ldGVzLWRhc2hib2FyZDprdWJlcm5ldGVzLWRhc2hib2FyZCJ9.OM17-TJwsRLmF1H-lTInnenwJ5mQKMkrpVzfJ-mx13g0Re4DUR45UrF4q52t7v7yIJNVfvOxQh6FsgbDe3prjqfCBJSe7_oiwnzD1HoShDPGje93wKKAA0faBRhjj2rVQaVM2vlytAYJ273er14zqhI4m5A_A1rKPYQP9kvdAb17QOyR-2uTW4UEwXcDVu1M79Y_Yu6xeHIElu9FzKCz2tNRSFCrs3smp20fxHgFbDMANM67A7lyMsL4orHrQPtgVC8Ax85aN9ARBamp3k6tIGKZ8OdEaXM0MXyFPRU82hBTZa3Bqbw52H0HyTRooQnaIFjhbxqYX_2lOdTI8xR63WiIqWDSoJQ3pRjlQzLtObTzHHlYwVmBMu1oPYFcJQ2KlZaWogXcPB518ACuBlRbrSKvsFDPGEgA-iTWIxMbGJn5Gqc-Xmm6OnbI40FTg2G9OsrH7k1ve4KUbDl7WpxdBxDsWWhw9if4I1zmHSeLaif6ydU8x39iRXEycGuoklSSuh5BOsvSNjaCTY43VyH_OelO2O8_Mg3UkvNntbQjSqef1MtKT7k6K1J0xrguisIRJO8I5VOvg4DT8zeoi7390At02c5GdzGgHGz86ZzYGDLc_914WOQyc7XJ4vgR6Hx70rDikeRkqBoOrMI8Jx4hVdqVvh5IVOUXbX5xXx7T_yY'
}

GET_PODS = '/api/v1/pod/{}?itemsPerPage=100&page=1&sortBy=d,creationTimestamp'
GET_LOG = '/api/v1/log/{}/{}?logFilePosition=end&offsetFrom=2000&offsetTo=2600'
GET_JOBS = '/api/v1/job/{}?itemsPerPage=100&page=1&sortBy=d,creationTimestamp'
DELAY = 1
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
RETRY = 3

init()
session = r.session()


def authorize(env: str, token: str):
    rsp = session.get(env + '/api/v1/csrftoken/login', verify=False)
    if rsp.status_code != 200:
        print('failed to get x-csrf token')
        exit(1)
    csrf = rsp.json()['token']
    headers = {'x-csrf-token': csrf}
    payload = {'token': token}
    rsp = session.post(env + '/api/v1/login', json=payload, headers=headers, verify=False)
    if rsp.status_code != 200:
        print('failed to get jwe token')
        exit(1)
    token = rsp.json()
    del token['errors']
    # session.cookies.set('jweToken', rsp.text)
    session.headers.update({"jwetoken": token['jweToken']})
    rsp = session.get(env + '/api/v1/login/status')
    if rsp.status_code != 200:
        print('failed to get status')
        exit(1)


def scale(env: str, deployment: str, namespace: str, count: str):
    rsp = session.put(env + f'/api/v1/scale/deployment/{namespace}/{deployment}/?scaleBy={count}',
                      data=count.encode('utf-8'),
                      headers={'content-type': 'application/json'},
                      verify=False)
    if rsp.status_code == 200:
        print('scale command accepted')
        exit(0)
    else:
        print('scale command failed')
        exit(1)


def get_data(url: str):
    tries = 0
    try:
        while tries < 2:
            rsp = session.get(url)
            if rsp.status_code == 200:
                return rsp.json()
            else:
                print(f'!!! response status code {rsp.status_code}')
                tries += 1
    except r.ConnectionError:
        print('!!! connection error')
        exit(1)
    except r.Timeout:
        print('!!! connection timeout')
        exit(1)
    except Exception as ex:
        print(ex)
        exit(1)
    print('!!! retries failed')
    exit(1)


def get_pods(env: str, namespace='default', verbose=False):
    rsp = get_data(env + GET_PODS.format(namespace))
    pods = {}
    if verbose:
        print(f'{"APP":30} | {"NAME":50} | {"STATUS":10} | {"VERSION":20}')
        print('-' * 144)
    errors = []
    for pod in rsp['pods']:
        try:
            app = pod['objectMeta']['labels']['app']
            pod_name = pod['objectMeta']['name']
            stat = pod['status']
            version = pod['objectMeta']['labels'].get('version')
            if version is None:
                version = '-'

            if verbose:
                print(
                    f"{Fore.RED if stat != 'Running' else Style.RESET_ALL}{app:30} |"
                    f" {pod_name:50} |"
                    f" {stat:10} |"
                    f" {version:20} ")
            if pods.get(app) is None:
                pods[app] = []
            pods[app].append({'name': pod_name,
                              'status': stat})
        except KeyError:
            errors.append(pod)
            continue
    return pods


def get_jobs(env: str, namespace='default', verbose=False):
    rsp = get_data(env + GET_JOBS.format(namespace))
    jobs = []
    errors = []
    for job in rsp['jobs']:
        name = job['objectMeta']['name']
        jobs.append(name)
        if verbose:
            print(name)
    return jobs


def save_logs(env: str, deployment: str, namespace='default'):
    all_pods = get_pods(env, namespace)
    pods = all_pods.get(deployment)
    for pod in pods:
        rsp = session.get(env + f'/api/v1/log/file/{namespace}/{pod["name"]}/{deployment}/?previous=false')
        if rsp.status_code == 200:
            with open(f'{pod["name"]}.log', 'wb') as f:
                f.write(rsp.content)
                print(f'log file {pod["name"]}.log saved')
        else:
            print(f'response status = {rsp.status_code}')


def get_color(counter: int):
    if counter == 0:
        return ''
    elif counter == 1:
        return Fore.BLUE
    elif counter == 2:
        return Fore.RED
    else:
        return Style.RESET_ALL


def get_logs(log_pods: list, namespace='default'):
    all_pods = get_pods(current_env, namespace=namespace)
    pod_names = []
    for deployment in log_pods:
        pods_list = all_pods[deployment]
        for ppp in pods_list:
            pod_names.append(ppp['name'])
    logs = []
    latest_log_ts = {}
    pod_count = 0
    prev_pod = '-'.join(pod_names[0].split('-')[:-1])
    for pod in pod_names:
        rsp = get_data(current_env + GET_LOG.format(namespace, pod))
        lg: list = rsp['logs'][5:]
        for r in lg:
            r['count'] = pod_count
            r['pod'] = pod
        logs += lg
        latest_log_ts[pod] = rsp['logs'][-1]['timestamp']
        if not pod.startswith(prev_pod):
            pod_count += 1
        prev_pod = '-'.join(pod_names[0].split('-')[:-1])
    sorted_logs = sorted(logs, key=lambda i: dt.datetime.strptime(i['timestamp'][0:-4], TIMESTAMP_FORMAT))
    for l in sorted_logs:
        print(get_color(l['count']) + l['content'] + Style.RESET_ALL)

    while True:
        time.sleep(DELAY)
        pod_count = 0
        logs = []
        prev_pod = '-'.join(pod_names[0].split('-')[:-2])
        for pod in pod_names:
            rsp = get_data(current_env + GET_LOG.format(namespace, pod))
            temp_logs = [i['timestamp'] for i in rsp['logs']]
            index = -1
            try:
                index = temp_logs.index(latest_log_ts[pod])
            except ValueError:
                pass
            new_logs = rsp['logs'][index + 1:-1]
            latest_log_ts[pod] = rsp['logs'][-1]['timestamp']
            for r in new_logs:
                r['count'] = pod_count
                r['pod'] = pod
            logs += new_logs
            if not pod.startswith(prev_pod):
                pod_count += 1
            prev_pod = '-'.join(pod_names[0].split('-')[:-1])
        sorted_logs = sorted(logs, key=lambda i: dt.datetime.strptime(i['timestamp'][0:-4], TIMESTAMP_FORMAT))
        for l in sorted_logs:
            print(get_color(l['count']) + l['content'] + Style.RESET_ALL)


def get_job_logs(job_name: str, namespace='default'):
    basic_job_name = '-'.join(job_name.split('-')[0:3])
    job_details_url = f'/api/v1/log/source/{namespace}/{job_name}/job'
    job_details = get_data(current_env + job_details_url)
    pod_names = job_details.get('podNames')
    for pod in pod_names:
        raw = get_data(current_env +
            f'/api/v1/log/{namespace}/{pod}/{basic_job_name}?logFilePosition=end&offsetFrom=2000&offsetTo=2600')
        for record in raw['logs']:
            print(record['content'])


parser = argparse.ArgumentParser(description='tool to get logs from kubernetes')
parser.add_argument('-e', '--env', help='selects environment to be used',
                    choices=['dev', 'cert', 'devfrt', 'certfrt', 'pro'])
parser.add_argument('-p', '--pods', help='gets list of currently running pods', action='store_true')
parser.add_argument('-j', '--jobs', help='gets list of jobs', action='store_true')
parser.add_argument('-d', '--debugjob', help='gets job logs', nargs='+')
parser.add_argument('-l', '--logs', help='gets logs from 1-3 pods', nargs='+')
parser.add_argument('-n', '--namespace', help='select env namespace', default='default', choices=['default', 'alfa'])
parser.add_argument('-s', '--scale', help='scale pods. Example: swp-app=2')
parser.add_argument('-f', '--file', help='save logs to file')
args = parser.parse_args().__dict__

current_env = KUBE.get(args.get('env').upper())
if current_env is None:
    print(Fore.RED + f'there is no such env {args.get("env")}')
    exit(1)
else:
    authorize(current_env, TOKEN[args.get('env').upper()])

# get pods
if args.get('pods'):
    pods = get_pods(current_env, namespace=args.get('namespace'), verbose=True)
    exit(0)

# get jobs
if args.get('jobs'):
    pods = get_jobs(current_env, namespace=args.get('namespace'), verbose=True)
    exit(0)

if args.get('scale'):
    param = args.get('scale')
    namespace = args.get('namespace')
    deployment, count = param.split('=')
    scale(current_env, deployment, namespace, count)

if args.get('file'):
    param = args.get('file')
    namespace = args.get('namespace')
    save_logs(current_env, param, namespace)
    exit(0)

if args.get('logs'):
    log_pods = args.get('logs')
    if log_pods:
        try:
            get_logs(log_pods, args.get('namespace'))
        except KeyboardInterrupt:
            exit(0)
        except Exception as ex:
            print(ex)
            exit(-1)

if args.get('debugjob'):
    jobs = args.get('debugjob')
    if jobs:
        try:
            get_job_logs(jobs[0])
        except KeyboardInterrupt:
            exit(0)
        except Exception as ex:
            print(ex)
            exit(-1)


