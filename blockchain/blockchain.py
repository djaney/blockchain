import hashlib as hasher
import time
import json

class Block:
    def __init__(self, index, timestamp, data, previous_hash, proof_of_work=None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.proof_of_work = proof_of_work
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "proof_of_work": self.proof_of_work,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }

    def compute_hash(self):
        sha = hasher.sha256()
        data = str(self.index)
        data += str(self.timestamp)
        data += str(self.data)
        data += str(self.previous_hash)
        data += str(self.proof_of_work)

        data = data.encode('utf-8')
        sha.update(data)

        return sha.hexdigest()


def create_genesis_block(proof_of_work=None):
    # Manually construct a block with
    # index zero and arbitrary previous hash
    return Block(0, time.time(), None, "0", proof_of_work)


def create_block(last_block, data, proof_of_work=None):
    this_index = last_block.index + 1
    this_timestamp = time.time()
    this_data = data
    this_hash = last_block.hash
    block = Block(this_index, this_timestamp, this_data, this_hash, proof_of_work=proof_of_work)
    return block


def verify_chain(chain):
    # TODO verify if transactions
    last_block_hash = None
    for block in reversed(chain):
        if last_block_hash is not None:
            if block.compute_hash() != last_block_hash:
                return False
        last_block_hash = block.previous_hash
    return True


def verify_new_block(chain, new_block):
    return verify_chain(chain + [new_block])


def chain_from_json(content):
    data = json.loads(content)
    chain = []
    for d in data:
        chain.append(dict_to_block(d))
    return chain


def dict_to_block(d):
    return Block(d.get("index"), d.get("timestamp"), d.get("data"), d.get("previous_hash"), d.get("proof_of_work"))
