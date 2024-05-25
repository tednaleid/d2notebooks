import queue
import http.server
import ssl
import threading
from urllib.parse import urlparse, parse_qs
import requests
import os
import base64
import queue
import webbrowser

class BungieAuth:
    def __init__(self, client_id):
        self.client_id = client_id
        self.redirect_url = "https://localhost:7777/"
        self.httpd = None
        self.server_thread = None
        self.token = None

    class RedirectHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            self.server.queue.put(query_params)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Access token transmitted to notebook. You can close this window now.')
            return

    def __create_https_server(self, port, certfile, keyfile, queue):
        self.httpd = http.server.HTTPServer(('localhost', port), self.RedirectHandler)
        self.httpd.queue = queue
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile, keyfile)
        self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.start()
        return self.httpd, self.server_thread

    def __stop_https_server(self):
        if self.httpd is None or self.server_thread is None:
            return
        print('Stopping HTTPS server')
        self.httpd.shutdown()
        self.httpd.socket.close()
        self.server_thread.join()

    def __pkce_verifier(self, length):
        return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')

    def __login_with_pkce(self, open_browser=True):
        q = queue.Queue()
        self.__create_https_server(7777, 'cert.pem', 'key.pem', q)

        state = self.__pkce_verifier(128)

        authorization_url = f"https://www.bungie.net/en/oauth/authorize?client_id={self.client_id}&response_type=code&state={state}&redirect_uri={self.redirect_url}"

        print(f"Please go to the following URL and authorize the app: {authorization_url}")

        if open_browser:
            webbrowser.open(authorization_url)

        query_params = q.get()

        self.__stop_https_server()

        code = query_params['code'][0]

        return code

    def __get_token_json(self, code):
        url = "https://www.bungie.net/platform/app/oauth/token/"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=data, headers=headers)
        return response.json()

    def refresh_oauth_token(self, open_browser=True):
        code = self.__login_with_pkce(open_browser)
        token_json = self.__get_token_json(code)
        self.token = token_json['access_token']
        return self.token