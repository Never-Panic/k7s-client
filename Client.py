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
    docker_client.images.pull(request.form['repository'])
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
    k8s_apps_v1 = client.AppsV1Api()
    k8s_apps_v1.create_namespaced_deployment(body=dep, namespace=request.form['namespace'])
    return 'create success'



