
import requests

class NodeRegistry:
    def __init__(self, bootstrap_url=None):
        self.peers = set()
        self.bootstrap_url = bootstrap_url
        if bootstrap_url:
            self.peers.add(bootstrap_url)
            self.discover_peers()

    def register_node(self, peer_url):
        if not peer_url.startswith('http://') and not peer_url.startswith('https://'):
            peer_url = f'http://{peer_url}'
        peer_url = peer_url.rstrip('/')
        self.peers.add(peer_url)
        print(f"Đã đăng ký node: {peer_url}")
        return peer_url

    def discover_peers(self):
        if not self.bootstrap_url:
            return
        try:
            response = requests.get(f'{self.bootstrap_url}/get_nodes', timeout=10)
            if response.status_code == 200:
                peers = response.json()['nodes']
                self.peers.update(peers)
                print(f"Đã khám phá peers: {self.peers}")
            else:
                print(f"Không lấy được peers từ {self.bootstrap_url}: {response.status_code}")
        except Exception as e:
            print(f"Lỗi khi khám phá peers: {str(e)}")

    def get_peers(self):
        return list(self.peers)

node_registry = NodeRegistry()