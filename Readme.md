# KDC - Kubernetes Dashboard Connector
Designed to partially replace kubectl app if your DevOps do not grant access to it.  
As an alternative for kubectl,
DevOps can set up [Kubernetes Dashboard](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)  
web app and grant access to it. But as this solution is slow and not very convenient, I've created this tool to request 
logs and pod data from the cluster.

## Features
- [x] select kubernetes cluster to work with
- [x] select kubernetes namespace to work with
- [x] list namespaces
- [x] list deployments
- [x] list pods
- [x] list jobs
- [x] get logs from pods by name pattern. Multiple pods can be selected separated by space
- [x] get logs from the latest job by name pattern
- [x] delete pod by name pattern (1 per time, check if it is allowed)
- [x] scale deployment by name pattern (1 per time, check if it is allowed)
- [x] download logs to the file
- [x] show the token of current cluster

## Installation
1. Clone the repository and open the terminal in the root folder (should have `pyproject.toml` file in it)
2. install the build tool ```pip install build```
3. run the build command ```python -m build```
4. install the package ```pip install dist/kdc-1.3.1-py3-none-any.whl```

It is planned the app to be published on PyPi, so the installation will be easier.
```bash
pip install kdc-kubeconnector
```

## Configuration
Find the config file here `~/.kdc/config.toml`
It will be created after the first run of the tool.  
```toml
[default]
cluster = "localhost"
namespace = "default"

[log]
level = "INFO"
file = "kdc.log"
save = false

[connection]
retries = 3
delay = 1

[cluster.localhost]
url = "http://localhost:8001"
token = "token"

[cluster.dev]
url = "http://dev:8001
token = "token2"

[cluster.uat]
url = "http://uat:8001
token = "token3"
```

## Usage Examples
List pods
```bash
kdc -p
kdc -p s=running --only running
kdc -p s=run  --only running
kdc -p n=nginx --only with name nginx
kdc -p s=run n=ngi with name nginx
```
Get logs from the pod with name like nginx-sd4353453-4543d
```bash
kdc -l nginx
```
Get logs from the few pods
```bash
kdc -l nginx app1 app2
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.