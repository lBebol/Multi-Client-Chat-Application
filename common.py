import json
import time

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
    """
    Receives a single JSON message from a socket.
    Blocks until a newline character is encountered.
    Returns the decoded Python dictionary.
    """
    buffer = ""
    while True:
        chunk = sock.recv(4096).decode("utf-8")
        if not chunk:
            # Socket closed
            return None

        buffer += chunk
        if "\n" in buffer:
            line, _, remainder = buffer.partition("\n")
            return json.loads(line)

# =========================
# Utility helpers
# =========================

def current_timestamp():
    """
    Returns the current Unix timestamp as an integer.
    """
    return int(time.time())
