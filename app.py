from flask import Flask, jsonify, request  # Flask để tạo API
import requests  # Gửi request đến các node khác trong mạng P2P
import os  # Xuất hành file
import hashlib  # Tạo mã hash
import json  # Lưu trữ dữ liệu blockchain
import time  # Thêm timestamp cho block
from blockchain import Blockchain  # Import class Blockchain từ file blockchain.py
from web3 import Web3
from eth_account import Account
from p2p import node_registry


# Kết nối với Ganache
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Địa chỉ contract của bạn sau khi deploy
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# ABI của smart contract (copy từ file JSON sau khi compile)
contract_abi = [{"anonymous": False , "inputs": [{"indexed": False , "internalType": "string", "name": "documentHash", "type": "string"}], "name": "DocumentStored", "type": "event"}, {"inputs": [{"internalType": "string", "name": "documentHash", "type": "string"}], "name": "storeDocument", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "string", "name": "documentHash", "type": "string"}], "name": "verifyDocument", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}]

# Load contract
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

if web3.is_connected():
    print("✅ Đã kết nối với Ethereum node!")
else:
    print("❌ Không thể kết nối với Ethereum node!")


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
    if 'file' not in request.files:
        return jsonify({'message': 'Không có file trong request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Không có file được chọn'}), 400

    file_content = file.read()
    document_hash = hashlib.sha256(file_content).hexdigest()
    block_index = blockchain.add_transaction(document_hash)
    
    # Broadcast giao dịch tới tất cả node
    for node in blockchain.nodes:
        try:
            requests.post(f'{node}/add_transaction', json={'document_hash': document_hash})
            print(f"Broadcast giao dịch tới {node}")
        except Exception as e:
            print(f"Lỗi khi broadcast giao dịch tới {node}: {str(e)}")

    # Tạo block nếu đủ giao dịch
    if len(blockchain.transactions) >= 1:
        previous_block = blockchain.get_previous_block()
        proof = blockchain.proof_of_work(previous_block['proof'])
        previous_hash = blockchain.hash_block(previous_block)
        new_block = blockchain.create_block(proof, previous_hash)
        
        # Broadcast block mới
        for node in blockchain.nodes:
            try:
                requests.post(f'{node}/add_block', json=new_block)
                print(f"Broadcast block tới {node}")
            except Exception as e:
                print(f"Lỗi khi broadcast block tới {node}: {str(e)}")

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
    # private_key = request.json.get('private_key')
    private_key = request.form.get('private_key')
    if not private_key:
        return jsonify({'message': 'Thiếu private key trong body'}), 400

    # Tạo đối tượng tài khoản từ private key
    try:
        # account = web3.eth.account.private_key_to_account(private_key)
        account = Account.from_key(private_key)
    except Exception as e:
        return jsonify({'message': 'Lỗi khi chuyển đổi private key', 'error': str(e)}), 500
    func_call = contract.functions.storeDocument(document_hash)
    print(type(func_call))  # kiểm tra có phải ContractFunction không
    # Gọi smart contract Ethereum để lưu document hash vào blockchain Ethereum
    # print(web3.eth.chain_id)
    try:
        # Tạo giao dịch
        transaction = contract.functions.storeDocument(document_hash).build_transaction({
            'chainId': 31337,  # Chain ID của mạng của bạn
            'gas': 100000,  # Gas limit (tùy chỉnh)
            'gasPrice': web3.to_wei('10', 'gwei'),
            'nonce': web3.eth.get_transaction_count(account.address),
        })

        # Ký giao dịch bằng private key
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

        # Gửi giao dịch đã ký
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Đợi giao dịch được xác nhận
        web3.eth.wait_for_transaction_receipt(tx_hash)

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
    

# 3️⃣ API xem toàn bộ blockchain
# @app.route('/get_chain', methods=['GET'])
# def get_chain():
#     return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200
@app.route('/get_chain', methods=['GET'])
def get_chain():
    # Thử đồng bộ chuỗi từ các node khác trước khi trả về
    blockchain.replace_chain()
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    print(blockchain.nodes)
    return jsonify({'nodes': node_registry.get_peers()}), 200


# 3️⃣ API tạo block mới
@app.route('/mine_block', methods=['POST'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash_block(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    
    # Broadcast block mới tới tất cả các node
    for node in blockchain.nodes:
        try:
            response = requests.post(f'{node}/add_block', json=block)
            print(f"Broadcast block tới {node}: {response.status_code}")
        except Exception as e:
            print(f"Lỗi khi broadcast tới {node}: {str(e)}")
    
    return jsonify(block), 200  

@app.route('/add_block', methods=['POST'])
def add_block():
    block = request.get_json()
    print(f"Nhận block mới: {block}")
    
    # Kiểm tra tính hợp lệ của block
    previous_block = blockchain.get_previous_block()
    if block['previous_hash'] != blockchain.hash_block(previous_block):
        print("Block không hợp lệ: previous_hash không khớp")
        return jsonify({'message': 'Block không hợp lệ'}), 400
    
    # Kiểm tra proof (nếu cần)
    if not blockchain.is_valid_proof(block['proof'], previous_block['proof']):
        print("Block không hợp lệ: proof không hợp lệ")
        return jsonify({'message': 'Block không hợp lệ'}), 400
    
    blockchain.chain.append(block)
    print("Block đã được thêm vào chuỗi")
    return jsonify({'message': 'Block đã được thêm vào chain'}), 200
# @app.route('/register_node', methods=['POST'])
# def register_node():
#     json_data = request.get_json()
#     node_url = json_data.get('node_url')
    
#     if node_url is None:
#         return jsonify({'message': 'Thiếu node_url'}), 400

#     # Thêm node vào mạng P2P
#     blockchain.add_node(node_url)
#     node_registry.register_node(node_url)

#     # Tự động đồng bộ chain từ các node khác
#     replaced = blockchain.replace_chain()
    
#     if replaced:
#         response = {
#             'message': 'Node đã được đăng ký và chain đã được đồng bộ với chain dài nhất',
#             'new_chain': blockchain.chain
#         }
#     else:
#         response = {
#             'message': 'Node đã được đăng ký, chain hiện tại đã là bản mới nhất',
#             'current_chain': blockchain.chain
#         }

#     return jsonify(response), 201
@app.route('/register_node', methods=['POST'])
def register_node():
    json_data = request.get_json()
    node_url = json_data.get('node_url')
    
    if not node_url:
        return jsonify({'message': 'Thiếu node_url'}), 400

    if not node_url.startswith('http://') and not node_url.startswith('https://'):
        node_url = f'http://{node_url}'
    
    try:
        blockchain.add_node(node_url)
        node_registry.register_node(node_url)
        print(f"Đã đăng ký node: {node_url}")

        replaced = blockchain.replace_chain()
        
        if replaced:
            response = {
                'message': 'Node đã được đăng ký và chuỗi đã được hợp nhất',
                'new_chain': blockchain.chain
            }
        else:
            response = {
                'message': 'Node đã được đăng ký, không có block mới để hợp nhất',
                'current_chain': blockchain.chain
            }
        return jsonify(response), 201
    except Exception as e:
        print(f"Lỗi khi đăng ký node {node_url}: {str(e)}")
        return jsonify({'message': 'Lỗi khi đăng ký node', 'error': str(e)}), 500


@app.route('/sync_chain', methods=['POST'])
def sync_chain():
    try:
        replaced = blockchain.replace_chain()
        if replaced:
            return jsonify({
                'message': 'Chuỗi đã được hợp nhất với tất cả block từ các node',
                'new_chain': blockchain.chain
            }), 200
        return jsonify({
            'message': 'Không có block mới để hợp nhất',
            'current_chain': blockchain.chain
        }), 200
    except Exception as e:
        print(f"Lỗi khi hợp nhất chuỗi: {str(e)}")
        return jsonify({'message': 'Lỗi khi hợp nhất chuỗi', 'error': str(e)}), 500


# 4️⃣ API thêm node vào mạng P2P
# @app.route('/connect_node', methods=['POST'])
# def connect_node():
#     json_data = request.get_json()
#     nodes = json_data.get('nodes')
#     if nodes is None:
#         return jsonify({'message': 'Không có node nào để kết nối'}), 400
#     for node in nodes:
#         blockchain.add_node(node)
#     return jsonify({'message': 'Kết nối thành công', 'nodes': list(blockchain.nodes)}), 201

# @app.route('/connect_node', methods=['POST'])
# def connect_node():
#     json_data = request.get_json()
#     nodes = json_data.get('nodes')
#     if nodes is None:
#         return "No nodes provided", 400
#     for node in nodes:
#         blockchain.add_node(node)
#     return jsonify({'message': 'All nodes connected successfully.', 'total_nodes': list(blockchain.nodes)}), 201


# 5️⃣ API đồng bộ dữ liệu giữa các node
# @app.route('/sync_chain', methods=['GET'])
# def sync_chain():
#     longest_chain = blockchain.chain
#     for node in blockchain.nodes:
#         response = requests.get(f'http://{node}/get_chain')
#         if response.status_code == 200:
#             data = response.json()
#             if len(data['chain']) > len(longest_chain) and blockchain.is_chain_valid(data['chain']):
#                 longest_chain = data['chain']
#     blockchain.chain = longest_chain
#     return jsonify({'message': 'Đã đồng bộ', 'chain': blockchain.chain}), 200

# @app.route('/sync_chain', methods=['GET'])
# def sync_chain():
#     longest_chain = blockchain.chain  # Chain hiện tại
#     for node in blockchain.nodes:  # Duyệt qua tất cả node đã biết
#         try:
#             response = requests.get(f'{node}/get_chain')  # Lấy chain từ node khác
#             if response.status_code == 200:
#                 other_chain = response.json()['chain']
#                 # Ưu tiên chain dài hơn và hợp lệ
#                 if len(other_chain) > len(longest_chain) and blockchain.is_chain_valid(other_chain):
#                     longest_chain = other_chain
#         except requests.exceptions.RequestException:
#             continue  # Bỏ qua node không phản hồi

#     # Cập nhật chain nếu tìm thấy chain dài hơn
#     if longest_chain != blockchain.chain:
#         blockchain.chain = longest_chain
#         return jsonify({'message': 'Đã đồng bộ chain', 'new_chain': longest_chain}), 200
#     else:
#         return jsonify({'message': 'Chain đã là bản mới nhất', 'chain': longest_chain}), 200


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000  # Lấy cổng từ tham số dòng lệnh
    app.run(host='0.0.0.0', port=port)
