import requests
# Danh sách node đã đăng ký
peers = set()

def register_node(peer_url):
    peers.add(peer_url)

def broadcast_new_block(block):
    for peer in peers:
        try:
            requests.post(f'{peer}/receive_block', json=block)
        except:
            continue

def broadcast_new_transaction(tx):
    for peer in peers:
        try:
            requests.post(f'{peer}/receive_transaction', json=tx)
        except:
            continue
