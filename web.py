from flask import Flask, jsonify, request
import blockchain
from broadcast import Broadcast
import os
import urllib.request
import urllib.error
import json
import time

PARENT = os.environ.get("PARENT")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")

flask_app = Flask(__name__)


class BlockBroadcast(Broadcast):

    def receive(self):
        data = request.data
        data_dict = json.loads(data)
        new_block = blockchain.dict_to_block(data_dict)
        self.node.receive_new_block(new_block)
        return '', 201


class WebNode(blockchain.Node):
    all_nodes = []

    def __init__(self, app, chain=None):
        super().__init__(chain=chain)

        self.block_broadcaster = BlockBroadcast('blx', app, self)

    def broadcast_new_block(self, new_block):
        json_bytes = json.dumps(new_block.to_dict()).encode('utf-8')
        self.block_broadcaster.send(json_bytes)

    def broadcast_new_transaction(self, transaction):
        pass  # TODO

    def add_peer(self, peer_host_port):
        if peer_host_port not in self.all_nodes:
            self.all_nodes.append(peer_host_port)


if PARENT is None:
    # create genesis
    web_node = WebNode(flask_app)
else:
    while True:
        # always retry
        try:
            contents = urllib.request.urlopen("http://{}/connect/{}/{}".format(PARENT, HOST, PORT)).read()
            break
        except urllib.error.URLError:
            time.sleep(1)

    contents_dict = json.loads(contents)

    # convert dict list to block list
    # create new node instance with chain
    web_node = WebNode(flask_app, chain=[blockchain.dict_to_block(b) for b in contents_dict["chain"]])
    # add parent as peer
    web_node.add_peer(PARENT)

    # add parent peers as own
    for p in contents_dict["nodes"]:
        web_node.add_peer(p)


@flask_app.route('/', methods=['GET'])
def index():
    return jsonify([c.to_dict() for c in web_node.chain])


@flask_app.route('/connect/<host>/<port>', methods=['GET'])
def connect(host, port):
    chain = [c.to_dict() for c in web_node.chain]
    response = jsonify({"chain": chain, "nodes": web_node.all_nodes})
    web_node.add_peer("{}:{}".format(host, port))

    return response


@flask_app.route('/peer', methods=['GET'])
def peer():
    return jsonify(web_node.all_nodes)


@flask_app.route('/trx', methods=['GET'])
def trx():
    web_node.add_transaction({"data": "test"})
    return '', 201


@flask_app.route('/mine', methods=['GET'])
def mine():
    web_node.mine()
    return '', 201
