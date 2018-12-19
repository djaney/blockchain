import urllib.request
import urllib.error


class Broadcast:
    def __init__(self, name, app, node):
        self.name = name
        self.app = app
        self.node = node
        self.app.add_url_rule('/b/{}'.format(self.name), 'broadcast_{}'.format(self.name), view_func=self.receive,
                              methods=['POST'])

    def receive(self):
        raise NotImplementedError



    def send(self, data):
        for n in self.node.all_nodes:
            try:
                req = urllib.request.Request("http://{}/b/{}".format(n, self.name))
                req.add_header('Content-Type', 'application/json; charset=utf-8')

                req.add_header('Content-Length', len(data))
                urllib.request.urlopen(req, data)
            except urllib.error.URLError:
                # remove host if it timed out
                self.node.all_nodes.remove(n)


