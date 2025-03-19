from flask import Flask, jsonify, request  # Flask để tạo API
import requests  # Gửi request đến các node khác trong mạng P2P
import hashlib  # Tạo mã hash
import json  # Lưu trữ dữ liệu blockchain
import time  # Thêm timestamp cho block
from blockchain import Blockchain  # Import class Blockchain từ file blockchain.py

app = Flask(__name__)
blockchain = Blockchain()

# 1️⃣ API tạo giao dịch mới
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json_data = request.get_json()
    if not json_data.get('document_hash'):
        return jsonify({'message': 'Thiếu dữ liệu'}), 400
    index = blockchain.add_transaction(json_data['document_hash'])
    return jsonify({'message': f'Tài liệu sẽ được ghi vào Block {index}'}), 201

# 2️⃣ API tạo block mới
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    proof = blockchain.proof_of_work(previous_block['proof'])
    previous_hash = blockchain.hash_block(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    return jsonify(block), 200

# 3️⃣ API xem toàn bộ blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

# 4️⃣ API thêm node vào mạng P2P
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json_data = request.get_json()
    nodes = json_data.get('nodes')
    if nodes is None:
        return jsonify({'message': 'Không có node nào để kết nối'}), 400
    for node in nodes:
        blockchain.add_node(node)
    return jsonify({'message': 'Kết nối thành công', 'nodes': list(blockchain.nodes)}), 201

# 5️⃣ API đồng bộ dữ liệu giữa các node
@app.route('/sync_chain', methods=['GET'])
def sync_chain():
    longest_chain = blockchain.chain
    for node in blockchain.nodes:
        response = requests.get(f'http://{node}/get_chain')
        if response.status_code == 200:
            data = response.json()
            if len(data['chain']) > len(longest_chain) and blockchain.is_chain_valid(data['chain']):
                longest_chain = data['chain']
    blockchain.chain = longest_chain
    return jsonify({'message': 'Đã đồng bộ', 'chain': blockchain.chain}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
