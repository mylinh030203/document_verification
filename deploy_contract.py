from web3 import Web3
import json

# Kết nối đến Ethereum Private Network (Ganache hoặc Geth)
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545/"))
web3.eth.default_account = web3.eth.accounts[0]

# Đọc Smart Contract đã biên dịch (ABI & Bytecode)
with open("D:\HK8\ChuyenDe\document_verification\compiled_abi.json") as f:
    abi = json.load(f)

with open("D:\HK8\ChuyenDe\document_verification\compiled_bytecode.json") as f:
    bytecode = f.read()

# Deploy Contract
contract = web3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = contract.constructor().transact()
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Lưu địa chỉ contract
contract_address = tx_receipt.contractAddress
print(f"Smart Contract deployed at: {contract_address}")
