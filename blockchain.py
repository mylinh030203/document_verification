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
        self.sync_on_init()  # Kiem tra va thay doi chain (15/4)

    def sync_on_init(self):     
        if len(self.nodes) > 0:
            self.replace_chain()

    # def sync_on_join(self, node_url):
    #     try:
    #         response = requests.get(f'{node_url}/get_chain', timeout=5)
    #         if response.status_code == 200:
    #             data = response.json()
    #             if data['length'] > len(self.chain) and self.is_chain_valid(data['chain']):
    #                 self.chain = data['chain']
    #                 return True
    #     except:
    #         pass
    #     return False

    def sync_on_join(self, node_url):
        try:
            response = requests.get(f'{node_url}/get_chain', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['length'] > len(self.chain) and self.is_chain_valid(data['chain']):
                    self.chain = data['chain']
                    print(f"Đã đồng bộ chuỗi từ {node_url}: length={data['length']}")
                    return True
        except Exception as e:
            print(f"Lỗi khi đồng bộ từ {node_url}: {str(e)}")
        return False

    # def create_block(self, proof, previous_hash):
    #     block = {
    #         'index': len(self.chain) + 1,
    #         'timestamp': time.time(),
    #         'transactions': self.transactions,
    #         'proof': proof,
    #         'previous_hash': previous_hash
    #     }
    #     self.transactions = []
    #     self.chain.append(block)
    #     return block

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
        print(f"Đã tạo block mới: index={block['index']}, timestamp={block['timestamp']}")
        return block

    def add_transaction(self, document_hash):
        self.transactions.append({'document_hash': document_hash})
        return self.chain[-1]['index'] + 1

    def get_previous_block(self):
        return self.chain[-1]

    # def proof_of_work(self, previous_proof):
    #     new_proof = 1
    #     while hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()[:4] != "0000":
    #         new_proof += 1
    #     return new_proof

    def proof_of_work(self, previous_proof):
        new_proof = 1
        difficulty = 4  # Số chữ số 0 yêu cầu
        target = '0' * difficulty
        while hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()[:difficulty] != target:
            new_proof += 1
        print(f"Đã tìm thấy proof: {new_proof}")
        return new_proof
    
    # def is_valid_proof(self, proof, previous_proof):
    #     hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
    #     return hash_operation[:4] == '0000'  # Kiểm tra proof hợp lệ

    def is_valid_proof(self, proof, previous_proof):
        hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        difficulty = 4
        target = '0' * difficulty
        is_valid = hash_operation[:difficulty] == target
        print(f"Kiểm tra proof: {'Hợp lệ' if is_valid else 'Không hợp lệ'}, hash={hash_operation}")
        return is_valid

    def hash_block(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    # def is_chain_valid(self, chain):
    #     for i in range(1, len(chain)):
    #         block = chain[i]
    #         previous_block = chain[i-1]
    #         if block['previous_hash'] != self.hash_block(previous_block):
    #             print(f"Chuỗi không hợp lệ: previous_hash không khớp tại block {i}")
    #             return False
    #         if not self.is_valid_proof(block['proof'], previous_block['proof']):
    #             print(f"Chuỗi không hợp lệ: proof không hợp lệ tại block {i}")
    #             return False
    #     return True

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
        print("Chuỗi hợp lệ")
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



    # def verify_document(self, document_hash):
    #     # Kiểm tra xem tài liệu có tồn tại trong các giao dịch đã lưu trong blockchain không
    #     for block in self.chain:
    #         for transaction in block['transactions']:
    #             if transaction['document_hash'] == document_hash:
    #                 return True  # Tài liệu không bị chỉnh sửa
    #     return False  # Tài liệu không tồn tại hoặc đã bị chỉnh sửa

    def verify_document(self, document_hash):
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['document_hash'] == document_hash:
                    print(f"Tìm thấy document_hash {document_hash} trong block {block['index']}")
                    return True
        print(f"Không tìm thấy document_hash {document_hash}")
        return False
    
# Đồng bộ chuỗi từ các node khác
    # def replace_chain(self):
    #     longest_chain = None
    #     max_length = len(self.chain)
        
    #     for node in self.nodes:
    #         try:
    #             response = requests.get(f'{node}/get_chain', timeout=10)
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 if data['length'] > max_length and self.is_chain_valid(data['chain']):
    #                     max_length = data['length']
    #                     longest_chain = data['chain']
    #         except:
    #             continue
                
    #     if longest_chain:
    #         self.chain = longest_chain
    #         return True
    #     return False

    # def replace_chain(self):
    #     longest_chain = None
    #     max_length = len(self.chain)
    #     for node in self.nodes:
    #         try:
    #             response = requests.get(f'{node}/get_chain', timeout=10)
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 if data['length'] > max_length and self.is_chain_valid(data['chain']):
    #                     max_length = data['length']
    #                     longest_chain = data['chain']
    #                     print(f"Tìm thấy chuỗi dài hơn từ {node}: length={max_length}")
    #                 else:
    #                     print(f"Chuỗi từ {node} không dài hơn hoặc không hợp lệ")
    #             else:
    #                 print(f"Phản hồi không thành công từ {node}: {response.status_code}")
    #         except Exception as e:
    #             print(f"Lỗi khi lấy chuỗi từ {node}: {str(e)}")
    #             continue

    #     if longest_chain:
    #         self.chain = longest_chain
    #         print(f"Đã thay thế chuỗi: length={max_length}")
    #         return True
    #     print("Không tìm thấy chuỗi dài hơn")
    #     return False

    def replace_chain(self):
        if len(self.chain) > 1:
            print("Chuỗi hiện tại đã có dữ liệu, không đồng bộ")
            return False

        # Ưu tiên đồng bộ từ bootstrap node
        bootstrap_url = "http://192.168.0.111:5000"
        try:
            response = requests.get(f'{bootstrap_url}/get_chain', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if self.is_chain_valid(data['chain']):
                    self.chain = data['chain']
                    print(f"Đã đồng bộ chuỗi từ bootstrap node {bootstrap_url}: length={data['length']}")
                    return True
                else:
                    print(f"Chuỗi từ {bootstrap_url} không hợp lệ")
            else:
                print(f"Phản hồi không thành công từ {bootstrap_url}: {response.status_code}")
        except Exception as e:
            print(f"Lỗi khi đồng bộ từ {bootstrap_url}: {str(e)}")

        # Thử các node khác nếu bootstrap node thất bại
        for node in self.nodes:
            if node == bootstrap_url:
                continue
            try:
                response = requests.get(f'{node}/get_chain', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if self.is_chain_valid(data['chain']):
                        self.chain = data['chain']
                        print(f"Đã đồng bộ chuỗi từ {node}: length={data['length']}")
                        return True
                    else:
                        print(f"Chuỗi từ {node} không hợp lệ")
                else:
                    print(f"Phản hồi không thành công từ {node}: {response.status_code}")
            except Exception as e:
                print(f"Lỗi khi đồng bộ từ {node}: {str(e)}")
                continue

        print("Không thể đồng bộ chuỗi từ bất kỳ node nào")
        return False