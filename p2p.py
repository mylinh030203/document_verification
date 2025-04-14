# p2p.py

import requests

class NodeRegistry:
    def __init__(self):
        self.peers = set()

    def register_node(self, peer_url):
        self.peers.add(peer_url)

    def get_peers(self):
        return list(self.peers)

    def broadcast_new_block(self, block):
        for peer in self.peers:
            try:
                requests.post(f'{peer}/receive_block', json=block)
            except requests.exceptions.RequestException:
                continue

    def broadcast_new_transaction(self, tx):
        for peer in self.peers:
            try:
                requests.post(f'{peer}/receive_transaction', json=tx)
            except requests.exceptions.RequestException:
                continue

# Tạo một thể hiện toàn cục của NodeRegistry
node_registry = NodeRegistry()
