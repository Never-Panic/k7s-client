from flask import Flask, jsonify, request
import docker

app = Flask(__name__)
client = docker.from_env()

@app.route("/list_images", methods=['GET'])
def list_images():
    images = client.images.list()
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
    client.images.remove(request.form["image_id"])
    return 'delete success'

'''
form data:
repository
'''
@app.route("/pull_image", methods=['POST'])
def pull_image():
    client.images.pull(request.form['repository'])
    return 'pull success'

'''
form data:
dockerfile: a file 
tag: text
'''
@app.route("/build_image", methods=['POST'])
def build_image():
    client.images.build(fileobj=request.files.get('dockerfile'), tag=request.form['tag'])
    return 'build success'



