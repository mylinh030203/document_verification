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
    
    def is_valid_proof(self, proof, previous_proof):
        hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        return hash_operation[:4] == '0000'  # Kiểm tra proof hợp lệ

    def hash_block(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        for i in range(1, len(chain)):
            block = chain[i]
            previous_block = chain[i-1]
            if block['previous_hash'] != self.hash_block(previous_block):
                print(f"Chuỗi không hợp lệ: previous_hash không khớp tại block {i}")
                return False
            if not self.is_valid_proof(block['proof'], previous_block['proof']):
                print(f"Chuỗi không hợp lệ: proof không hợp lệ tại block {i}")
                return False
        return True




    def add_node(self, node_url):
    # Chuẩn hóa URL
        if not node_url.startswith('http://') and not node_url.startswith('https://'):
            node_url = f'http://{node_url}'
        # Loại bỏ dấu / cuối nếu có
        node_url = node_url.rstrip('/')
        if node_url not in self.nodes:
            self.nodes.add(node_url)
            print(f"Đã thêm node: {node_url}")

    def verify_document(self, document_hash):
        # Kiểm tra xem tài liệu có tồn tại trong các giao dịch đã lưu trong blockchain không
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['document_hash'] == document_hash:
                    return True  # Tài liệu không bị chỉnh sửa
        return False  # Tài liệu không tồn tại hoặc đã bị chỉnh sửa
    
# Đồng bộ chuỗi từ các node khác
    def replace_chain(self):
        print("Bắt đầu hợp nhất chuỗi...")
        # Thu thập tất cả giao dịch từ chuỗi hiện tại
        all_transactions = []
        for block in self.chain:
            all_transactions.extend(block['transactions'])

        # Thu thập giao dịch từ các node khác
        for node in self.nodes:
            print(f"Kiểm tra node: {node}")
            try:
                response = requests.get(f'{node}/get_chain', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    chain = data['chain']
                    for block in chain:
                        for tx in block['transactions']:
                            if tx not in all_transactions:  # Tránh trùng lặp
                                all_transactions.append(tx)
                    print(f"Thu thập {len(chain)} block từ node {node}")
                else:
                    print(f"Yêu cầu tới {node} thất bại với mã: {response.status_code}")
            except Exception as e:
                print(f"Lỗi khi kết nối tới {node}: {str(e)}")

        if not all_transactions:
            print("Không có giao dịch mới để hợp nhất")
            return False

        # Xây dựng chuỗi mới
        new_chain = []
        self.chain = []  # Xóa chuỗi cũ
        self.create_block(proof=1, previous_hash='0')  # Tạo lại block genesis
        new_chain.append(self.chain[0])

        # Thêm tất cả giao dịch vào các block mới
        transactions_per_block = 1  # Số giao dịch mỗi block
        for i in range(0, len(all_transactions), transactions_per_block):
            self.transactions = all_transactions[i:i + transactions_per_block]
            previous_block = self.get_previous_block()
            proof = self.proof_of_work(previous_block['proof'])
            previous_hash = self.hash_block(previous_block)
            new_block = self.create_block(proof, previous_hash)
            new_chain.append(new_block)

        # Xác thực chuỗi mới
        if self.is_chain_valid(new_chain):
            print("Chuỗi hợp nhất hợp lệ, thay thế chuỗi hiện tại")
            self.chain = new_chain
            return True
        else:
            print("Chuỗi hợp nhất không hợp lệ, giữ chuỗi hiện tại")
            return False