import datetime as dt


def _parse_pods_response(response: dict, name_filter: str = '', status_filter: str = '') -> list:
    pods = list()
    for pod in response['pods']:
        p = {'status': 'unknown', 'restarts': 'unknown', 'name': 'unknown', 'appLabel': 'unknown', 'created': 'unknown'}
        # this code will skip the pods that are not possible to parse
        try:
            p['status'] = pod['status']
            p['restarts'] = pod['restartCount']
            p['name'] = pod['objectMeta']['name']
            p['created'] = pod['objectMeta']['creationTimestamp']
            p['appLabel'] = pod['objectMeta']['labels'].get('app')
        except Exception:
            pass  # it is done in purpose to avoid corrupted pod data to crash the app
        finally:
            pods.append(p)
    # filtering part
    pods = [pod for pod in pods if name_filter.lower() in pod['name'].lower()]
    pods = [pod for pod in pods if status_filter.lower() in pod['status'].lower()]
    return pods


def _parse_jobs_response(response: dict) -> list:
    jobs = list()
    for job in response['jobs']:
        j = {'name': 'unknown', 'status': 'unknown', 'created': 'created'}
        try:
            j['name'] = job['objectMeta']['name']
            j['status'] = job['jobStatus']['status']
            j['created'] = job['objectMeta']['creationTimestamp']
        except Exception:
            pass  # it is done in purpose to avoid corrupted pod data to crash the app
        finally:
            jobs.append(j)
    return jobs


def _parse_deployments_response(response: dict) -> list:
    deployments = list()
    for deployment in response['deployments']:
        d = {'name': 'unknown', 'created': 'unknown', 'desired_pods': 'unknown', 'running_pods': 'unknown'}
        try:
            d['name'] = deployment['objectMeta']['name']
            d['created'] = deployment['objectMeta']['creationTimestamp']
            d['desired_pods'] = deployment['pods']['desired']
            d['running_pods'] = deployment['pods']['running']
        except Exception:
            pass  # it is done in purpose to avoid corrupted pod data to crash the app
        finally:
            deployments.append(d)
    deployments.sort(key=lambda x: x['name'])
    return deployments


def _parse_raw_logs(raw_logs: list, name: str, offset=None) -> list:
    logs = list()
    for log in raw_logs:
        timestamp = log['timestamp'][0:23]
        content = log['content']
        ts = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        logs.append((ts, name, content))

    logs.sort(key=lambda x: x[0])
    if offset:
        logs = [log for log in logs if log[0] > offset]
    return logs


def _parse_namespaces(response: dict) -> list:
    namespaces = list()
    for ns in response['namespaces']:
        n = {'name': 'unknown', 'phase': 'unknown', 'uid': 'unknown'}
        try:
            n['name'] = ns['objectMeta']['name']
            n['phase'] = ns['phase']
            n['uid'] = ns['objectMeta']['uid']
        except Exception:
            pass  # it is done in purpose to avoid corrupted pod data to crash the app
        finally:
            namespaces.append(n)
    return namespaces
