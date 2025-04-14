import hashlib
import json
import time
from flask import Flask, jsonify, request
import requests
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.nodes = set()
        self.create_block(proof=1, previous_hash='0')  # Tạo block genesis

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, document_hash):
        self.transactions.append({'document_hash': document_hash})
        return self.chain[-1]['index'] + 1

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()[:4] != "0000":
            new_proof += 1
        return new_proof

    def hash_block(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        for block in chain[1:]:
            if block['previous_hash'] != self.hash_block(previous_block):
                return False
            if not self.is_proof_valid(previous_block['proof'], block['proof']):
                return False
            previous_block = block
        return True



    def add_node(self, address):
        self.nodes.add(address)
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def verify_document(self, document_hash):
        # Kiểm tra xem tài liệu có tồn tại trong các giao dịch đã lưu trong blockchain không
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['document_hash'] == document_hash:
                    return True  # Tài liệu không bị chỉnh sửa
        return False  # Tài liệu không tồn tại hoặc đã bị chỉnh sửa
    
# Đồng bộ chuỗi từ các node khác
def replace_chain(self):
    longest_chain = self.chain
    max_length = len(self.chain)

    for node in self.nodes:
        try:
            response = requests.get(f'{node}/chain')
            if response.status_code == 200:
                data = response.json()
                length = len(data['chain'])  # Lấy chain từ response
                chain = data['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        except:
            continue

    self.chain = longest_chain
    return True

