# abouzeid
import socket
import threading
import json

class ClientNet:
    def __init__(self, on_message=None, on_disconnect=None):
        """
        on_message(msg_dict): called when a message is received
        on_disconnect(): called when connection is lost
        """
        self.sock = None
        self.receiver_thread = None
        self.running = False

        self.on_message = on_message
        self.on_disconnect = on_disconnect

    # -------------------- Connection --------------------
    def connect(self, server_ip, port, username):
        """
        Connect to server and perform login
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_ip, port))

        # Send login message
        login_msg = {
            "type": "login",
            "username": username
        }
        self.send_json(login_msg)

        # Start receiver thread
        self.running = True
        self.receiver_thread = threading.Thread(
            target=self.receive_loop,
            daemon=True
        )
        self.receiver_thread.start()

    # -------------------- Receiving --------------------
    def receive_loop(self):
        """
        Background thread that listens for messages
        """
        try:
            while self.running:
                msg = self.recv_json()
                if msg is None:
                    break

                if self.on_message:
                    self.on_message(msg)

        except Exception as e:
            print("Receive error:", e)

        finally:
            self.running = False
            if self.on_disconnect:
                self.on_disconnect()

    # -------------------- Sending --------------------
    def send_group_message(self, text):
        """
        Send a group chat message
        """
        msg = {
            "type": "group_message",
            "text": text
        }
        self.send_json(msg)

    def send_private_message(self, target, text):
        """
        Send a private message to a user
        """
        msg = {
            "type": "private_message",
            "target": target,
            "text": text
        }
        self.send_json(msg)

    # -------------------- Disconnect --------------------
    def disconnect(self):
        """
        Close connection gracefully
        """
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass

    # -------------------- JSON Helpers --------------------
    def send_json(self, data):
        """
        Send JSON object with newline delimiter
        """
        message = json.dumps(data).encode("utf-8") + b"\n"
        self.sock.sendall(message)

    def recv_json(self):
        """
        Receive a single JSON message
        """
        buffer = b""
        while b"\n" not in buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            buffer += chunk

        line, _, rest = buffer.partition(b"\n")
        return json.loads(line.decode("utf-8"))
