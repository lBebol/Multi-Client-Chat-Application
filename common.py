import json
import time

_socket_buffers = {}

# =========================
# Message type constants
# =========================

MSG_LOGIN = "login"
MSG_LOGIN_OK = "login_ok"
MSG_ERROR = "error"

MSG_GROUP = "group"
MSG_PRIVATE = "private"
MSG_SYSTEM = "system"

MSG_HISTORY_REQUEST = "history_request"
MSG_HISTORY_RESPONSE = "history_response"

MSG_USERLIST = "userlist"

# =========================
# JSON socket helpers
# =========================

def send_json(sock, data):
    """
    Sends a Python dictionary as a JSON message over a socket.
    A newline character is appended to mark the end of the message.
    """
    message = json.dumps(data) + "\n"
    sock.sendall(message.encode("utf-8"))


def recv_json(sock):
    buf = _socket_buffers.get(sock, "")

    while True:
        if "\n" in buf:
            line, _, rest = buf.partition("\n")
            _socket_buffers[sock] = rest
            return json.loads(line)

        chunk = sock.recv(4096)
        if not chunk:
            _socket_buffers.pop(sock, None)
            return None

        buf += chunk.decode("utf-8")
        _socket_buffers[sock] = buf

# =========================
# Utility helpers
# =========================

def current_timestamp():
    """
    Returns the current Unix timestamp as an integer.
    """
    return int(time.time())
