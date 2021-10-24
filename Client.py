from flask import Flask, jsonify, request
import docker
from kubernetes import client, config
import yaml

# set flask
app = Flask(__name__)

# set k8s client
config.load_kube_config()

# set docker client
docker_client = docker.from_env()

#######################
# image 
#######################

@app.route("/list_images", methods=['GET'])
def list_images():
    images = docker_client.images.list()
    arr = []
    for image in images:
        dic = {}
        dic["attrs"] = image.attrs
        dic["id"] = image.id
        dic["labels"] = image.labels
        dic["short_id"] = image.short_id
        dic["tags"] = image.tags
        arr.append(dic)
    return jsonify(arr)

'''
image_id: text
'''
@app.route("/remove_image", methods=['POST'])
def remove_image():
    docker_client.images.remove(request.form["image_id"])
    return 'delete success'

'''
repository: text
'''
@app.route("/pull_image", methods=['POST'])
def pull_image():
    docker_client.images.pull(repository=request.form['repository'])
    return 'pull success'

'''
dockerfile: a file 
tag: text
'''
@app.route("/build_image", methods=['POST'])
def build_image():
    docker_client.images.build(fileobj=request.files.get('dockerfile'), tag=request.form['tag'])
    return 'build success'

#######################
# container
#######################

@app.route("/list_containers", methods=['GET'])
def list_containers():
    containers = docker_client.containers.list()
    arr = []
    for container in containers: 
        dic = {}
        dic["id"] = container.id
        dic['name'] = container.name
        dic['image'] = {'id': container.image.id,'tags': container.image.tags}
        dic["labels"] = container.labels
        dic["short_id"] = container.short_id
        dic["status"] = container.status
        arr.append(dic)
    return jsonify(arr)

'''
image: str
name: str
command[]: list of str
environment[]: list of str
host_posts[]: list of int
container_ports[]: list of str
volumes[]: list of str
'''
@app.route("/run_container", methods=['POST'])
def run_container():
    command = request.values.getlist('command[]')
    environment = request.values.getlist('environment[]')
    container_ports = request.values.getlist('container_ports[]')
    host_posts = request.values.getlist('host_posts[]')
    volumes = request.values.getlist('volumes[]')

    ports = {}
    for cp, hp in zip(container_ports, host_posts):
        ports[cp] = hp

    docker_client.containers.run(image=request.form['image'], name=request.form['name'], command=command, 
                                environment=environment, ports=ports,volumes=volumes, detach=True)
    return 'create success'

'''
container_id: str
new_name: str
'''
@app.route("/rename_container", methods=['POST'])
def rename_container():
    container = docker_client.containers.get(request.form['container_id'])
    container.rename(request.form['new_name'])
    return 'rename success'

'''
container_id: str
'''
@app.route("/restart_container", methods=['POST'])
def restart_container():
    container = docker_client.containers.get(request.form['container_id'])
    container.restart()
    return 'restart success'

'''
container_id: str
'''
@app.route("/start_container", methods=['POST'])
def start_container():
    container = docker_client.containers.get(request.form['container_id'])
    container.start()
    return 'start success'

'''
container_id: str
'''
@app.route("/stop_container", methods=['POST'])
def stop_container():
    container = docker_client.containers.get(request.form['container_id'])
    container.stop()
    return 'stop success'

'''
container_id: str
'''
@app.route("/remove_container", methods=['POST'])
def remove_container():
    container = docker_client.containers.get(request.form['container_id'])
    container.remove()
    return 'remove success'

'''
container_id: str
repository: str
tag: str
message: str
author: str
changes: str
'''
@app.route("/commit_container", methods=['POST'])
def commit_container():
    container = docker_client.containers.get(request.form['container_id'])

    changes = None
    if 'changes' in request.form: changes = request.form['changes']

    container.commit(repository=request.form['repository'], tag=request.form['tag'], message=request.form['message'],
                    author=request.form['author'], changes=changes)
    return 'commit success'

#######################
# k8s
#######################

@app.route("/list_nodes", methods=['GET'])
def list_nodes():
    ret = client.CoreV1Api().list_node()
    arr = []
    for i in ret.items:
        dic = {}
        dic['kind'] = i.kind
        dic['name'] = i.metadata.name
        dic['namespace'] = i.metadata.namespace
        dic['creation_timestamp'] = i.metadata.creation_timestamp
        dic['allocatable'] = i.status.allocatable
        dic['phase'] = i.status.phase
        arr.append(dic)
    return jsonify(arr)

@app.route("/list_pods", methods=['GET'])
def list_pods():
    ret = client.CoreV1Api().list_pod_for_all_namespaces(watch=False)
    arr = []
    for i in ret.items:
        dic={}
        dic['namespace'] = i.metadata.namespace
        dic['name'] = i.metadata.name
        dic['creation_timestamp'] = i.metadata.creation_timestamp
        dic['pod_ip'] = i.status.pod_ip
        container_statuses = []
        for status in i.status.container_statuses:
            s = {}
            s['name'] = status.name
            s['container_id'] = status.container_id
            s['image_id'] = status.image_id
            s['image'] = status.image
            s['ready'] = status.ready
            container_statuses.append(s)
        dic['container_statuses'] = container_statuses
        dic['node_name'] = i.spec.node_name
        arr.append(dic)
    return jsonify(arr)

######### deployment ######### 

@app.route("/list_deployments", methods=['GET'])
def list_deployments():
    ret = client.AppsV1Api().list_deployment_for_all_namespaces()
    arr = []
    for i in ret.items:
        dic={}
        dic['name'] = i.metadata.name
        dic['creation_timestamp'] = i.metadata.creation_timestamp
        dic['namespace'] = i.metadata.namespace
        dic['available_replicas'] = i.status.available_replicas
        dic['replicas'] = i.status.replicas
        arr.append(dic)
    return jsonify(arr)

'''
name: text
namespace: text
'''
@app.route("/delete_deployment", methods=['POST'])
def delete_deployment():
    client.AppsV1Api().delete_namespaced_deployment(name=request.form['name'], namespace=request.form['namespace'])
    return 'delete success'

'''
namespace: text
config: a yaml file
'''
@app.route("/create_deployment", methods=['POST'])
def create_deployment():
    dep = yaml.safe_load(request.files.get('config'))
    client.AppsV1Api().create_namespaced_deployment(body=dep, namespace=request.form['namespace'])
    return 'create success'

######### service ######### 

@app.route("/list_services", methods=['GET'])
def list_services():
    ret = client.CoreV1Api().list_service_for_all_namespaces()
    arr = []
    for i in ret.items:
        dic={}
        dic['name'] = i.metadata.name
        dic['creation_timestamp'] = i.metadata.creation_timestamp
        dic['namespace'] = i.metadata.namespace
        dic['cluster_ip'] = i.spec.cluster_ip
        dic['external_i_ps'] = i.spec.external_i_ps
        dic['type'] = i.spec.type
        ports = []
        for p in i.spec.ports:
            tem = {}
            tem['node_port'] = p.node_port
            tem['port'] = p.port
            tem['protocol'] = p.protocol
            ports.append(tem)
        dic['ports'] = ports
        arr.append(dic)
    return jsonify(arr)

'''
namespace: text
config: a yaml file
'''
@app.route("/create_service", methods=['POST'])
def create_service():
    dep = yaml.safe_load(request.files.get('config'))
    client.CoreV1Api().create_namespaced_service(body=dep, namespace=request.form['namespace'])
    return 'create success'

'''
name: text
namespace: text
'''
@app.route("/delete_service", methods=['POST'])
def delete_service():
    client.CoreV1Api().delete_namespaced_service(name=request.form['name'], namespace=request.form['namespace'])
    return 'delete success'

