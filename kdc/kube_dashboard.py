import time
import requests
from requests import Response
import logging
import urllib3
import datetime as dt
from kdc.parsers import _parse_pods_response, _parse_jobs_response, _parse_deployments_response, _parse_raw_logs, \
    _parse_namespaces

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def connection_decorator(func):
    def wrapper(self, *args, **kwargs):
        for _ in range(self.retry):
            try:
                result = func(self, *args, **kwargs)
                if result.status_code == 200:
                    return result
                elif result.status_code == 401:
                    self.authorize()
                    continue
                elif result.status_code == 404:
                    self.log.error(self.error_message.format(result.request.url))
                    raise Exception('Failed to connect after retries')
                else:
                    self.log.error(f'Requested URL {result.request.url} returned {result.status_code}')
                    time.sleep(self.delay)
                    continue
            except requests.exceptions.RequestException as e:
                self.log.error(f'Failed to connect to {self.url}: {e}')
                time.sleep(self.delay)
        self.log.error(f'Failed to connect to {self.url} after {self.retry} retries')
        raise Exception('Failed to connect after retries')

    return wrapper


class KubeDashboard:
    def __init__(self, name: str, url: str, token: str, **kwargs):
        self.name = name
        self.url = url
        self.token = token
        self.session = requests.Session()
        self.log = logging.getLogger('KDC')

        self.retry = kwargs.get('retry', 3)
        self.timeout = kwargs.get('timeout', 10)
        self.delay = kwargs.get('delay', 1)
        self.namespace = kwargs.get('namespace', 'default')
        self.log_page = kwargs.get('page', 2000)

    def authorize(self):
        rsp = self.session.get(self.url + '/api/v1/csrftoken/login', verify=False)
        self.log.debug('Requested x-csrf token URL: ' + rsp.request.url)
        if rsp.status_code != 200:
            raise Exception('failed to get x-csrf token')

        csrf = rsp.json().get('token')
        headers = {'x-csrf-token': csrf}
        payload = {'token': self.token}

        rsp = self.session.post(self.url + '/api/v1/login', json=payload, headers=headers, verify=False)
        self.log.debug('Requested jwe token URL: ' + rsp.request.url)
        if rsp.status_code != 200:
            raise Exception('failed to get jwe token')

        token = rsp.json()
        self.session.headers.update({"jwetoken": token['jweToken']})
        rsp = self.session.get(self.url + '/api/v1/login/status')
        self.log.debug('Requested login status URL: ' + rsp.request.url)
        if rsp.status_code != 200:
            raise Exception('failed to get status')

    @connection_decorator
    def get(self, endpoint: str, **kwargs) -> Response:
        return self.session.get(self.url + endpoint, verify=False, **kwargs)

    def get_pods(self, name_filter: str = '', status_filter: str = '') -> list:
        rsp = self.get(f'/api/v1/pod/{self.namespace}',
                       params={'itemsPerPage': 100,
                               'page': 1,
                               'sortBy': 'd,creationTimestamp'}
                       )
        self.log.debug('Requested get pods URL: ' + rsp.request.url)
        pods = _parse_pods_response(rsp.json(), name_filter, status_filter)
        return pods

    def get_jobs(self) -> list:
        rsp = self.get(f'/api/v1/job/{self.namespace}',
                       params={'itemsPerPage': 30,
                               'page': 1,
                               'sortBy': 'd,creationTimestamp'}
                       )
        self.log.debug('Requested get jobs URL: ' + rsp.request.url)
        jobs = _parse_jobs_response(rsp.json())
        return jobs

    def get_deployments(self) -> list:
        rsp = self.get(f'/api/v1/deployment/{self.namespace}',
                       params={'itemsPerPage': 100,
                               'page': 1,
                               'sortBy': 'd,creationTimestamp'}
                       )
        self.log.debug('Requested get deployments URL: ' + rsp.request.url)
        deployments = _parse_deployments_response(rsp.json())
        return deployments

    def scale_deployment(self, deployment_name: str, replicas: int):
        rsp = self.session.put(
            self.url + f'/api/v1/scale/deployment/{self.namespace}/{deployment_name}/?scaleBy={replicas}',
            json={'scaleBy': replicas},
            headers={'content-type': 'application/json'},
            verify=False
        )
        if rsp.status_code != 200:
            self.log.error(f'failed to scale deployment {deployment_name} to {replicas} replicas')
        else:
            self.log.info(f'deployment {deployment_name} scaled to {replicas} replicas')

    def delete_pod(self, pod_name: str):
        rsp = self.session.delete(
            self.url + f'/api/v1/_raw/pod/namespace/{self.namespace}/name/{pod_name}',
            verify=False
        )
        if rsp.status_code != 200:
            self.log.error(f'failed to delete pod {pod_name}')
        else:
            self.log.info(f'pod {pod_name} deleted')

    def get_pod_logs(self, name: str, offset: dt.datetime = None) -> list:
        rsp = self.get(f'/api/v1/log/{self.namespace}/{name}',
                       params={'logFilePosition': 'end', 'offsetTo': self.log_page})
        return _parse_raw_logs(rsp.json()['logs'], name, offset)

    def get_job_logs(self, pod_name: str, container_name: str, offset: dt.datetime = None) -> list:
        rsp = self.get(f'/api/v1/log/{self.namespace}/{pod_name}/{container_name}',
                       params={'logFilePosition': 'end', 'offsetTo': self.log_page})
        return _parse_raw_logs(rsp.json()['logs'], pod_name, offset)

    def tail_pods_logs(self, *pod_patterns: str):
        pods = self.get_pods()
        pod_names = [p['name'] for p in pods if any(pattern in p['name'] for pattern in pod_patterns)]
        if len(pod_names) == 0:
            self.log.warning(f'No pods found for patterns: {pod_patterns}')
            return

        pointer = dict()
        for name in pod_names:
            pointer[name] = None
        while True:
            general_log = list()
            for name in pod_names:
                logs = self.get_pod_logs(name, pointer[name])
                for log in logs:
                    general_log.append(log)
                pointer[name] = logs[-1][0] if logs else pointer[name]
            general_log.sort(key=lambda x: x[0])
            for log in general_log:
                self.log.info(f'{log[1]} - {log[2]}')
            time.sleep(self.delay)

    def tail_latest_job_logs(self, job_pattern: str):
        jobs = self.get_jobs()
        job_name = ''
        for job in jobs:
            if job_pattern in job['name']:
                job_name = job['name']
                break

        if job_name == '':
            self.log.warning(f'No jobs found for patterns: {job_pattern}')
            return

        # get job details
        rsp = self.get(f'/api/v1/log/source/{self.namespace}/{job_name}/job')
        self.log.debug('Requested job details URL: ' + rsp.request.url)
        # TODO expected 1 container inside the job
        container_name = rsp.json()['containerNames'][0]
        pod_name = rsp.json()['podNames'][0]

        pointer = None
        while True:
            logs = self.get_job_logs(pod_name, container_name, pointer)
            pointer = logs[-1][0] if logs else pointer
            for log in logs:
                self.log.info(f'{log[1]} - {log[2]}')
            time.sleep(self.delay)

    def scale_deploy(self, pattern: str, replicas: int):
        deployments = self.get_deployments()
        for deployment in deployments:
            if pattern in deployment['name']:
                self.scale_deployment(deployment['name'], replicas)
                break

    def delete_pods(self, pattern: str):
        pods = self.get_pods()
        for pod in pods:
            if pattern in pod['name']:
                self.delete_pod(pod['name'])
                break

    def save_logs(self, *pod_patterns: str):
        pods = self.get_pods()
        pods = [p for p in pods if any(pattern in p['name'] for pattern in pod_patterns)]
        if len(pods) == 0:
            self.log.warning(f'No pods found for patterns: {pod_patterns}')
            return

        self.log.warning('request to download logs can take a while. Please wait and be patient')
        for pod in pods:
            pod_name = pod['name']
            pod_label = pod['appLabel']
            self.log.info(f'downloading logs for pod: {pod_name}')
            rsp = self.get(f'/api/v1/log/file/{self.namespace}/{pod_name}/{pod_label}/?previous=false')
            with open(f'{pod["name"]}.log', 'wb') as f:
                f.write(rsp.content)
            self.log.info('all logs are saved into the current directory')

    def get_namespaces(self) -> list:
        rsp = self.get(f'/api/v1/namespace')
        self.log.debug('Requested get namespaces URL: ' + rsp.request.url)
        namespaces = _parse_namespaces(rsp.json())
        return namespaces
