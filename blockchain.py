import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from collections import OrderedDict
import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

MINING_SENDER = 'GOPHER COIN'


class Blockchain:
    def __init__(self):
        self.transactions = []
        self.chain = []
        self.nodes = set()
        self.node_id = node_identifier
        # Genesis block
        self.new_block(proof=100, previous_hash='1')

    # Create a new block in the blockchain
    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.transactions = []
        self.chain.append(block)
        return block

    # create hash of block for unique identifiers
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # to slow down mining(would like to make this a game later)
    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while self.valid_proof(last_proof, last_hash, proof) is False:
            proof += 1

        return proof

    # validate proof against last accepted proof
    @staticmethod
    def valid_proof(last_proof, last_hash, proof):
        guess = f'{last_proof}{last_hash}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        print(guess_hash)
        return guess_hash[:4] == '0000'

    # Check to see if given blockchain is valid
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n-----------\n')
            last_hash = self.hash(last_block)
            if block['previous_hash'] != last_hash:
                return False

            proof = block['proof']
            last_proof = last_block['proof']
            if not self.valid_proof(last_proof, last_hash, proof):
                print('valid proof fail')
                return False
            last_block = block
            current_index += 1

        return True

    # Concensus algo to keep longest chain
    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbors:
            # print('http://' + node + '/chain')
            response = requests.get('http://' + node + '/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    # add a new node to list of nodes
    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    # Allow people to send blocks
    def new_transaction(self, sender, recipient, amount, signature):
        transaction = OrderedDict({'sender': sender,
                                   'recipient': recipient,
                                   'amount': amount})
        if sender == MINING_SENDER:
            self.transactions.append(transaction)
            return len(self.chain) + 1
        else:
            transaction_verification = self.verify_transaction_signature(
                sender, signature, transaction)
            if transaction_verification:
                self.transactions.append(transaction)
                return len(self.chain) + 1
            else:
                return False

    # Check that signature matches that of transaction
    def verify_transaction_signature(self, sender, signature, transaction):
        public_key = RSA.importKey(binascii.unhexify(sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(transaction).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(signature))

    @property
    def last_block(self):
        return self.chain[-1]


# Instantiate the Node
app = Flask(__name__)
CORS(app)

# Create unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate Blockchain
blockchain = Blockchain()

# -------- ROUTES --------- #


# @app.route('/')
# def index():
#     return render_template('./index.html')

# Get ma chain, yo!
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# mine for new blocks
@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.chain[-1]
    proof = blockchain.proof_of_work(last_block)

    # use transaction to send miner new block from server(sender: 0)
    blockchain.new_transaction(
        sender=MINING_SENDER,
        recipient=blockchain.node_id,
        amount=1,
        signature=''
    )

    # add new block to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged!',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


# register new nodes that have been mined
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return 'Error: please supply a valid list of nodes', 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

# route for creating a new transaction
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']

    if not all(k in values for k in required):
        return ' Missing values', 400

    transaction_result = blockchain.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount'],
        values['signature'])

    if transaction_result == False:
        response = {'message': 'Invalid Transaction!'}
        return jsonify(response), 406
    else:
        response = {
            'message': f'Transaction will be added to Block {transaction_result}'}
        return jsonify(response), 201


@app.route('/transactions/get', methods=['GET'])
def get_transations():
    transactions = blockchain.transactions
    response = {'transactions': transactions}
    return jsonify(response), 200

# Perform concesus checks for incoming chains to keep up to date
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replace',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes, }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p',  '--port',
                        default=5000,
                        type=int,
                        help='port to listen on')
    args = parser.parse_args()
    port = args.port

app.run(host='127.0.0.1', port=port)
