import unittest
import blockchain


class BlockChainTest(unittest.TestCase):
    def test_clean_block(self):

        chain = [blockchain.create_genesis_block()]
        for _ in range(1):
            new_block = blockchain.create_block(chain[-1], "Hello, this is a block")
            chain.append(new_block)

        self.assertTrue(blockchain.verify_chain(chain))

    def test_dirty_block(self):
        chain = [blockchain.create_genesis_block()]
        for _ in range(10):
            new_block = blockchain.create_block(chain[-1], "Hello, this is a block")
            chain.append(new_block)

        chain[3].data = "Tampered data"

        self.assertFalse(blockchain.verify_chain(chain))

    def test_clean_new_block(self):

        chain = [blockchain.create_genesis_block()]

        for _ in range(10):
            new_block = blockchain.create_block(chain[-1], "Hello, this is a block")
            chain.append(new_block)

        new_block = blockchain.create_block(chain[-1], "Hello, this is a block")
        self.assertTrue(blockchain.verify_new_block(chain, new_block))

    def test_dirty_new_block(self):

        chain = [blockchain.create_genesis_block()]

        for _ in range(10):
            new_block = blockchain.create_block(chain[-1], "Hello, this is a block")
            chain.append(new_block)

        chain[3].data = "Hello"

        new_block = blockchain.create_block(chain[-1], "Hello, this is a bad new block")
        self.assertFalse(blockchain.verify_new_block(chain, new_block))


class TestNode(blockchain.Node):
    all_nodes = []

    def broadcast_new_block(self, new_block):
        for n in self.all_nodes:
            if n is not self:
                n.receive_new_block(new_block)

    def broadcast_new_transaction(self, transaction):
        for n in self.all_nodes:
            if n is not self:
                n.receive_new_transaction(transaction)


class NetworkTest(unittest.TestCase):
    def test_network(self):
        nodes = [TestNode()]
        for _ in range(10):
            nodes.append(TestNode(chain=nodes[-1].chain))

        # add reference to all nodes
        for n in nodes:
            n.all_nodes = nodes

        # add transaction
        nodes[0].add_transaction({"data": "transaction#1"})
        # add transaction from another node
        nodes[1].add_transaction({"data": "transaction#2"})

        # all nodes should have one genesis block
        for n in nodes:
            self.assertEqual(1, len(n.chain))

        # mine
        for n in nodes:
            n.mine()

        # after mining all the transaction should be added
        self.assertEqual(2, len(nodes[0].chain))
        self.assertEqual(2, len(nodes[0].chain[1].data))

        # after mining the transactions should be empty
        for n in nodes:
            self.assertEqual(0, len(n.transactions))

        # chains should be identical and valid
        h = None
        for n in nodes:
            if h is None:
                h = n.chain[-1].hash
            self.assertTrue(blockchain.verify_chain(n.chain))
            self.assertEqual(h, n.chain[-1].hash)

        # verify transaction data
        for n in nodes:
            self.assertEqual(None, n.chain[0].data)
            self.assertEqual("transaction#1", n.chain[1].data[0]['data'])
            self.assertEqual("transaction#2", n.chain[1].data[1]['data'])

    def test_forks(self):
        node1 = TestNode()
        node2 = TestNode(chain=node1.chain)

        node1.all_nodes = node2.all_nodes = [node1, node2]

        # create new block for node 1
        new_block = blockchain.create_block(node1.chain[-1], [blockchain.add_transaction_meta({"data": "A"})])
        node1.chain.append(new_block)

        # create also block for node 2
        # new_block = blockchain.create_block(node2.chain[-1], "B")
        # node2.chain.append(new_block)

        # test if chain is still valid
        self.assertTrue(blockchain.verify_chain(node1.chain))
        self.assertTrue(blockchain.verify_chain(node2.chain))

        # test what happens if node 2 creates his own block
        node2.add_transaction({"data": "B"})
        node2.mine()

        # now we have 2 different hashes
        self.assertEqual(node1.chain[-1].previous_hash, node2.chain[-1].previous_hash)
        self.assertNotEqual(node1.chain[-1].hash, node2.chain[-1].hash)

        # adding transaction C and mining it in node 2 should make node 1 identical to node 2
        node2.add_transaction({"data": "C"})
        node2.mine()
        self.assertEqual(node1.chain[-1].hash, node2.chain[-1].hash)
        self.assertTrue(blockchain.verify_chain(node1.chain))
        self.assertTrue(blockchain.verify_chain(node2.chain))

    def test_json_to_chain(self):
        test_data = '[{"data":null,"hash":"d3cef8091a8cc8755f9e8410d987126f605da534c741bba73ba6f32190d5f64b",' \
                    '"index":0,"previous_hash":"0","proof_of_work":1,"timestamp":1544007383.3500865}]'
        chain = blockchain.chain_from_json(test_data)

        self.assertEqual(1, len(chain))
        self.assertEqual(None, chain[0].data)
        self.assertEqual("d3cef8091a8cc8755f9e8410d987126f605da534c741bba73ba6f32190d5f64b", chain[0].hash)
        self.assertEqual(0, chain[0].index)
        self.assertEqual("0", chain[0].previous_hash)
        self.assertEqual(1, chain[0].proof_of_work)
        self.assertEqual(1544007383.3500865, chain[0].timestamp)


if __name__ == '__main__':
    unittest.main()
