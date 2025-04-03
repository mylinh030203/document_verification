from flask import Flask, jsonify, request  # Flask để tạo API
import requests  # Gửi request đến các node khác trong mạng P2P
import os  # Xuất hành file
import hashlib  # Tạo mã hash
import json  # Lưu trữ dữ liệu blockchain
import time  # Thêm timestamp cho block
from blockchain import Blockchain  # Import class Blockchain từ file blockchain.py
from web3 import Web3

# Kết nối với Ganache
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Địa chỉ contract của bạn sau khi deploy
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# ABI của smart contract (copy từ file JSON sau khi compile)
contract_abi = [{"anonymous": False , "inputs": [{"indexed": False , "internalType": "string", "name": "documentHash", "type": "string"}], "name": "DocumentStored", "type": "event"}, {"inputs": [{"internalType": "string", "name": "documentHash", "type": "string"}], "name": "storeDocument", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "string", "name": "documentHash", "type": "string"}], "name": "verifyDocument", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}]

# Load contract
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

app = Flask(__name__)
blockchain = Blockchain()
# Đảm bảo thư mục lưu trữ file đã tồn tại
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# # 1️⃣ API lưu document hash vào blockchain nội bộ
# lưu tài liệu quan trọng vào blockchain nội bộ (chỉ có các nhân viên trong công ty mới check được)
@app.route('/store_document', methods=['POST'])
def store_document():
    # Kiểm tra xem file có trong request hay không
    if 'file' not in request.files:
        return jsonify({'message': 'Không có file trong request'}), 400

    file = request.files['file']
    
    # Kiểm tra nếu không có file được chọn
    if file.filename == '':
        return jsonify({'message': 'Không có file được chọn'}), 400

    # Đọc nội dung của file để tạo hash
    file_content = file.read()
    document_hash = hashlib.sha256(file_content).hexdigest()  # Tạo hash từ nội dung file

    # Lưu document_hash vào blockchain
    block_index = blockchain.add_transaction(document_hash)  # Thêm hash vào blockchain

    # Kiểm tra nếu số lượng giao dịch đạt một mức độ nào đó, bạn có thể tạo một block mới
    if len(blockchain.transactions) >= 1:  # Ví dụ tạo block khi có ít nhất 1 giao dịch
        previous_block = blockchain.get_previous_block()
        previous_proof = previous_block['proof']
        proof = blockchain.proof_of_work(previous_proof)
        previous_hash = blockchain.hash_block(previous_block)
        blockchain.create_block(proof, previous_hash)

    return jsonify({
        'message': 'Tài liệu đã được lưu vào blockchain',
        'file_hash': document_hash,
        'block_index': block_index
    }), 201

# 2️⃣ API lưu tài liệu trên Ethereum
@app.route('/store_on_ethereum', methods=['POST'])
def store_on_ethereum():
    # Kiểm tra xem file có trong request hay không
    if 'file' not in request.files:
        return jsonify({'message': 'Không có file trong request'}), 400

    # Lấy file từ request
    file = request.files['file']
    
    # Kiểm tra nếu không có file được chọn
    if file.filename == '':
        return jsonify({'message': 'Không có file được chọn'}), 400

    # Đọc nội dung của file để tạo hash
    try:
        file_content = file.read()
        document_hash = hashlib.sha256(file_content).hexdigest()  # Tạo hash từ nội dung file
    except Exception as e:
        return jsonify({'message': 'Lỗi khi đọc file', 'error': str(e)}), 500

    # Lấy private key từ JSON body
    private_key = request.json.get('private_key')
    if not private_key:
        return jsonify({'message': 'Thiếu private key trong body'}), 400

    # Tạo đối tượng tài khoản từ private key
    try:
        account = web3.eth.account.privateKeyToAccount(private_key)
    except Exception as e:
        return jsonify({'message': 'Lỗi khi chuyển đổi private key', 'error': str(e)}), 500

    # Gọi smart contract Ethereum để lưu document hash vào blockchain Ethereum
    try:
        # Tạo giao dịch
        transaction = contract.functions.storeDocument(document_hash).buildTransaction({
            'chainId': 31337,  # Chain ID của mạng của bạn
            'gas': 10000,  # Gas limit (tùy chỉnh)
            'gasPrice': web3.toWei('10', 'gwei'),
            'nonce': web3.eth.getTransactionCount(account.address),
        })

        # Ký giao dịch bằng private key
        signed_txn = web3.eth.account.signTransaction(transaction, private_key)

        # Gửi giao dịch đã ký
        tx_hash = web3.eth.sendRawTransaction(signed_txn.rawTransaction)

        # Đợi giao dịch được xác nhận
        web3.eth.waitForTransactionReceipt(tx_hash)

        # Trả về thông tin giao dịch
        return jsonify({
            'message': 'Tài liệu đã được lưu vào Ethereum',
            'file_hash': document_hash,
            'ethereum_transaction_hash': tx_hash.hex()
        }), 201

    except Exception as e:
        return jsonify({'message': 'Lỗi khi lưu vào Ethereum', 'error': str(e)}), 500
# @app.route('/add_transaction', methods=['POST'])
# def add_transaction():
#     json_data = request.get_json()
#     if not json_data.get('document_hash'):
#         return jsonify({'message': 'Thiếu dữ liệu'}), 400
#     index = blockchain.add_transaction(json_data['document_hash'])
#     return jsonify({'message': f'Tài liệu sẽ được ghi vào Block {index}'}), 201

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

# 6️⃣ API kiểm tra tài liệu trên blockchain nội bộ
@app.route('/verify_document', methods=['POST'])
def verify_document():
    # Kiểm tra tài liệu trên blockchain nội bộ
    if 'file' not in request.files:
        return jsonify({'message': 'Không có file trong request'}), 400

    file = request.files['file']

    # Kiểm tra nếu không có file được chọn
    if file.filename == '':
        return jsonify({'message': 'Không có file được chọn'}), 400

    try:
        # Đọc nội dung của file để tạo hash
        file_content = file.read()
        document_hash = hashlib.sha256(file_content).hexdigest()  # Tạo hash từ nội dung file

        # Kiểm tra tài liệu trên blockchain nội bộ
        if blockchain.verify_document(document_hash):
            return jsonify({'message': 'Tài liệu không bị chỉnh sửa trên blockchain nội bộ', 'document_hash': document_hash}), 200
        else:
            return jsonify({'message': 'Tài liệu đã bị chỉnh sửa hoặc không tồn tại trên blockchain nội bộ', 'document_hash': document_hash}), 400

    except Exception as e:
        return jsonify({'message': 'Lỗi khi kiểm tra tài liệu', 'error': str(e)}), 500

# 7️⃣ API kiểm tra tài liệu trên Ethereum
@app.route('/verify_on_ethereum', methods=['POST'])
def verify_on_ethereum():
    # Kiểm tra xem file có trong request hay không
    if 'file' not in request.files:
        return jsonify({'message': 'Không có file trong request'}), 400

    file = request.files['file']

    # Kiểm tra nếu không có file được chọn
    if file.filename == '':
        return jsonify({'message': 'Không có file được chọn'}), 400

    try:
        # Đọc nội dung của file để tạo hash
        file_content = file.read()
        document_hash = hashlib.sha256(file_content).hexdigest()  # Tạo hash từ nội dung file

        # Kiểm tra hash này có tồn tại trong blockchain Ethereum
        is_stored = contract.functions.verifyDocument(document_hash).call()

        if is_stored:
            return jsonify({'message': 'Tài liệu không bị chỉnh sửa trên Ethereum', 'document_hash': document_hash}), 200
        else:
            return jsonify({'message': 'Tài liệu đã bị chỉnh sửa hoặc không tồn tại trên Ethereum', 'document_hash': document_hash}), 400

    except Exception as e:
        return jsonify({'message': 'Lỗi khi kiểm tra tài liệu trên Ethereum', 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
