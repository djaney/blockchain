from flask import Flask, jsonify, request
import blockchain
import os
import urllib.request
import urllib.error
import json
import time

PARENT = os.environ.get("PARENT")
HOST = os.environ.get("HOST")
PORT = os.environ.get("PORT")

app = Flask(__name__)


class WebNode(blockchain.Node):
    all_nodes = []

    def broadcast_new_block(self, new_block):
        for n in self.all_nodes:
            try:
                req = urllib.request.Request("http://{}/blx".format(n))
                req.add_header('Content-Type', 'application/json; charset=utf-8')

                json_bytes = json.dumps(new_block.to_dict()).encode('utf-8')
                req.add_header('Content-Length', len(json_bytes))
                urllib.request.urlopen(req, json_bytes)
            except urllib.error.URLError:
                # remove host if it timed out
                self.all_nodes.remove(n)


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
        except urllib.error.URLError:
            time.sleep(1)

    contents_dict = json.loads(contents)

    # convert dict list to block list
    chain = [blockchain.dict_to_block(b) for b in contents_dict["chain"]]

    # create new node instance with chain
    node = WebNode(chain)
    # add parent as peer
    node.add_peer(PARENT)

    # add parent peers as own
    for p in contents_dict["nodes"]:
        node.add_peer(p)

@app.route('/', methods=['GET'])
def index():
    return jsonify([c.to_dict() for c in node.chain])

@app.route('/connect/<host>/<port>', methods=['GET'])
def connect(host, port):
    chain = [c.to_dict() for c in node.chain]
    response = jsonify({"chain": chain, "nodes": node.all_nodes})
    node.add_peer("{}:{}".format(host, port))

    return response

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
