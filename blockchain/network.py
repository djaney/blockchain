from blockchain import create_genesis_block, create_block, verify_new_block
import time
import uuid
import threading


class Node:

    def __init__(self, chain=None):

        self.chain_lock = threading.Lock()
        self.trans_lock = threading.Lock()
        if chain is None:
            self.chain = [create_genesis_block(proof_of_work=1)]
        else:
            self.chain = chain.copy()
        self.forks = {}
        self.transactions = []

    def add_transaction(self, trans):
        with self.trans_lock:
            add_transaction_meta(trans)
            self.transactions.append(trans)
        self.broadcast_new_transaction(trans)

    def mine(self):

        if len(self.transactions) == 0:
            return None

        # solve for proof of work
        answer = solve_proof_of_work(self.chain[-1])

        # get a copy of the transactions and flush the buffer
        with self.trans_lock:
            transactions = self.transactions.copy()
            self.transactions = []

        # remove existing transactions
        with self.chain_lock:
            existing_transactions_id_list = []
            for b in self.chain:
                if b.data is not None:
                    for t in b.data:
                        existing_transactions_id_list.append(t["id"])
        valid_transactions = []
        for t in transactions:
            if t["id"] not in existing_transactions_id_list:
                valid_transactions.append(t)
        transactions = valid_transactions

        # sort transactions
        transactions.sort(key=lambda i: i["time"])

        # create new block
        new_block = create_block(self.chain[-1], transactions, proof_of_work=answer)

        # validate and add new block
        self.chain_lock.acquire()
        if is_new_block_valid(self.chain, new_block):
            self.chain.append(new_block)
            self.chain_lock.release()
            self.broadcast_new_block(new_block)
        else:
            self.chain_lock.release()

    def receive_new_block(self, new_block):
        """if received block is valid, add it to chain and broadcast again"""

        self.chain_lock.acquire()

        if is_new_block_valid(self.chain, new_block):
            # block is valid
            self.chain.append(new_block)
            self.forks = {}
            self.chain_lock.release()
            self.broadcast_new_block(new_block)
        elif new_block.previous_hash in self.forks.keys() and \
                is_new_block_valid(self.chain[:-1] + [self.forks[new_block.previous_hash]], new_block):
            # append from fork
            self.chain = self.chain[:-1] + [self.forks[new_block.previous_hash], new_block]
            self.forks = {}
            self.chain_lock.release()
            self.broadcast_new_block(new_block)
        elif new_block.hash not in self.forks.keys() and is_new_block_valid(self.chain[:-1], new_block):
            # block is valid as fork
            self.forks[new_block.hash] = new_block
            self.chain_lock.release()
            self.broadcast_new_block(new_block)
        else:
            # block is invalid
            self.chain_lock.release()

    def receive_new_transaction(self, transaction):
        """recieve transactions"""
        with self.trans_lock:
            self.transactions.append(transaction)

    def broadcast_new_transaction(self, transaction):
        """broadcast newly created block to other nodes"""
        raise NotImplementedError

    def broadcast_new_block(self, new_block):
        """broadcast newly created block to other nodes"""
        raise NotImplementedError


def add_transaction_meta(trans):
    trans["time"] = time.time()
    trans["id"] = str(uuid.uuid1())
    return trans


def solve_proof_of_work(last_block):
    last_block_proof = last_block.proof_of_work

    if last_block_proof is None:
        answer = 1
        last_block_proof = 1
    else:
        answer = last_block_proof + 1

    while not (answer % 9 == 0 and answer % last_block_proof == 0):
        answer += 1
    return answer


def validate_proof_of_work(last_block, new_block):
    proof_of_work = new_block.proof_of_work
    last_block_proof_of_work = last_block.proof_of_work
    return proof_of_work % 9 == 0 and proof_of_work % last_block_proof_of_work == 0


def is_new_block_valid(chain, new_block):
    # if chain[-1].index != new_block.index - 1:
    #     return False

    if not verify_new_block(chain, new_block):
        return False

    # verify if proof of work checks out
    if not validate_proof_of_work(chain[-1], new_block):
        return False

    return True
