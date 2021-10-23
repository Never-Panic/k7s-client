from flask import Flask, jsonify, request
import docker
from kubernetes import client, config

# set flask
app = Flask(__name__)

# set k8s client
config.load_kube_config()

# set docker client
docker_client = docker.from_env()

#######################
# docker 
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
form data:
image_id
'''
@app.route("/remove_image", methods=['POST'])
def remove_image():
    docker_client.images.remove(request.form["image_id"])
    return 'delete success'

'''
form data:
repository
'''
@app.route("/pull_image", methods=['POST'])
def pull_image():
    docker_client.images.pull(request.form['repository'])
    return 'pull success'

'''
form data:
dockerfile: a file 
tag: text
'''
@app.route("/build_image", methods=['POST'])
def build_image():
    docker_client.images.build(fileobj=request.files.get('dockerfile'), tag=request.form['tag'])
    return 'build success'

#######################
# k8s
#######################

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
        arr.append(dic)
    return jsonify(arr)

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

