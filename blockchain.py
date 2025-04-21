import hashlib
import json
import time
from flask import Flask, jsonify, request
import requests
from urllib.parse import urlparse
from utils import get_local_ip

class Blockchain:
    def __init__(self, port=5000):
        self.chain = []
        self.transactions = []
        self.nodes = set()
        self.port = port  # Lưu port
        self.create_block(proof=1, previous_hash='0')
        self.sync_on_init()

    def sync_on_init(self):     
        if len(self.nodes) > 0:
            self.replace_chain()

    def sync_on_join(self, node_url):
        try:
            response = requests.get(f'{node_url}/get_chain', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['length'] > len(self.chain) and self.is_chain_valid(data['chain']):
                    self.chain = data['chain']
                    return True
        except:
            pass
        return False

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
    
# # Đồng bộ chuỗi từ các node khác
#     def replace_chain(self):
#         longest_chain = None
#         max_length = len(self.chain)
        
#         for node in self.nodes:
#             try:
#                 response = requests.get(f'{node}/get_chain', timeout=20)
#                 if response.status_code == 200:
#                     data = response.json()
#                     if data['length'] > max_length and self.is_chain_valid(data['chain']):
#                         max_length = data['length']
#                         longest_chain = data['chain']
#             except:
#                 continue
                
#         if longest_chain:
#             self.chain = longest_chain
#             return True
#         return False

    def replace_chain(self):
        longest_chain = None
        max_length = len(self.chain)
        
        # Lấy URL của node hiện tại
        current_node = f'http://{get_local_ip()}:{self.port}'
        print(f"Bắt đầu đồng bộ chuỗi, nodes: {self.nodes}, current_node: {current_node}")
        
        for node in self.nodes:
            if node == current_node:
                print(f"Bỏ qua node hiện tại: {node}")
                continue
            try:
                print(f"Đang gửi GET /get_chain tới {node}")
                response = requests.get(f'{node}/get_chain', timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Chuỗi từ {node}: length={data['length']}")
                    if data['length'] > max_length and self.is_chain_valid(data['chain']):
                        max_length = data['length']
                        longest_chain = data['chain']
                        print(f"Tìm thấy chuỗi dài hơn từ {node}: length={max_length}")
                else:
                    print(f"Phản hồi không thành công từ {node}: {response.status_code}")
            except Exception as e:
                print(f"Lỗi khi lấy chuỗi từ {node}: {str(e)}")
                continue
                
        if longest_chain:
            print(f"Thay thế chuỗi bằng chuỗi dài hơn: length={max_length}")
            self.chain = longest_chain
            return True
        print("Không tìm thấy chuỗi dài hơn")
        return False