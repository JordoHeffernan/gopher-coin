from collections import OrderedDict
import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request, render_template


# Transaction class for generating and validating transactions with keys
class Transaction:
    def __init__(self, sender, sender_private_key, recipient, amount):
        self.sender = sender
        self.sender_private_key = sender_private_key
        self.recipient = recipient
        self.amount = amount

    def __getattr__(self, attr):
        return self.data[attr]

    # Return transaction information as list without private key
    def to_dict(self):
        return OrderedDict({'sender': self.sender,
                            'recipient': self.recipient,
                            'amount': self.amount})

    # Add private key to transaction
    def sign_transaction(self):
        private_key = RSA.importKey(
            binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')


app = Flask(__name__)

# Provide new Private/public key pairings
@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    response = {
        'private_key':
        binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key':
        binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }
    return jsonify(response), 200

# Generate a new transaction given data from sender
@app.route('/transactions/generate', methods=['POST'])
def generate_transaction():

    sender = request.json['sender']
    sender_private_key = request.json['sender_private_key']
    recipient = request.json['recipient']
    amount = request.json['amount']

    transaction = Transaction(sender, sender_private_key, recipient, amount)

    response = {'transaction': transaction.to_dict(),
                'signature': transaction.sign_transaction()}

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

app.run(host='127.0.0.1', port=port)

# THESE ARE UNUSED ROUTES FOR FUTURE FRONTEND
# @app.route('/')
# def index():
#     return render_template('./index.html')

# @app.route('/make/transaction')
# def make_transaction():
#     return render_template('./make_transaction.html')

# @app.route('/view/transactions')
# def view_transaction():
#     return render_template('./view_transactions.html')
