from flask import Flask, jsonify, request
import blockchain
import os
import urllib.request
import json

PARENT = os.environ.get("PARENT")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")

app = Flask(__name__)


class WebNode(blockchain.Node):
    all_nodes = []

    def broadcast_new_block(self, new_block):
        for n in self.all_nodes:
            req = urllib.request.Request("http://{}/blx".format(n))
            req.add_header('Content-Type', 'application/json; charset=utf-8')

            json_bytes = json.dumps(new_block.to_dict()).encode('utf-8')
            req.add_header('Content-Length', len(json_bytes))
            urllib.request.urlopen(req, json_bytes)

    def broadcast_new_transaction(self, transaction):
        pass  # TODO

    def add_peer(self, peer_host_port):
        if peer_host_port not in self.all_nodes:
            self.all_nodes.append(peer_host_port)


if PARENT is None:
    # create genesis
    node = WebNode()
else:
    while True:
        # always retry
        try:
            contents = urllib.request.urlopen("http://{}/connect/{}/{}".format(PARENT, HOST, PORT)).read()
            break
        except Exception:
            pass

    node = WebNode(blockchain.chain_from_json(contents))
    node.add_peer(PARENT)


@app.route('/', methods=['GET'])
def index():
    return jsonify([c.to_dict() for c in node.chain])

@app.route('/connect/<host>/<port>', methods=['GET'])
def connect(host, port):
    node.add_peer("{}:{}".format(host, port))
    return jsonify([c.to_dict() for c in node.chain])

@app.route('/peer', methods=['GET'])
def peer():
    return jsonify(node.all_nodes)


@app.route('/trx', methods=['GET'])
def trx():
    node.add_transaction({"data": "test"})
    return '', 201


@app.route('/mine', methods=['GET'])
def mine():
    node.mine()
    return '', 201


@app.route('/blx', methods=['POST'])
def blx():
    data = request.data
    data_dict = json.loads(data)
    new_block = blockchain.dict_to_block(data_dict)
    node.receive_new_block(new_block)
    return '', 201
