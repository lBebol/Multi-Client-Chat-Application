import socket
import threading

from common import (
    send_json,
    recv_json,
    current_timestamp,
    MSG_LOGIN,
    MSG_LOGIN_OK,
    MSG_ERROR,
    MSG_GROUP,
    MSG_PRIVATE,
)

# =========================
# Internal client state
# =========================

_sock = None
_receiver_thread = None
_stop_event = threading.Event()
_is_connected = False

_on_message = None   # callback(msg_dict)
_on_status = None    # callback(status_str, details_str_optional)

_state_lock = threading.Lock()


# =========================
# Small internal helpers
# =========================

def _set_status(status, details=""):
    """
    Calls the status callback if provided.
    status examples: 'connected', 'disconnected', 'error', 'info'
    """
    if _on_status:
        try:
            _on_status(status, details)
        except Exception:
            # Never let UI/CLI callback errors crash networking
            pass


def _safe_close_socket():
    global _sock
    if _sock is not None:
        try:
            _sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            _sock.close()
        except Exception:
            pass
        _sock = None


# =========================
# Public API
# =========================

def connect(server_ip, port, username, on_message=None, on_status=None, timeout=8):
    """
    Connects to the server and performs login.
    Starts a background receiver thread.

    Parameters:
      - server_ip, port: where the server is running
      - username: desired username (must be unique)
      - on_message: function(msg_dict) called when a message arrives
      - on_status: function(status, details) called for connection events
      - timeout: socket timeout for initial connect
    """
    global _sock, _receiver_thread, _is_connected, _on_message, _on_status

    _on_message = on_message
    _on_status = on_status

    # Reset stop flag if reused
    _stop_event.clear()

    # Create socket + connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((server_ip, int(port)))
    except Exception as e:
        _safe_close_socket()
        _set_status("error", f"Failed to connect: {e}")
        return False
    finally:
        # After connect, go back to blocking mode for normal reads
        try:
            s.settimeout(None)
        except Exception:
            pass

    _sock = s

    # Send login
    try:
        send_json(_sock, {
            "type": MSG_LOGIN,
            "username": username,
            "ts": current_timestamp()
        })
    except Exception as e:
        _safe_close_socket()
        _set_status("error", f"Failed to send login: {e}")
        return False

    # Wait for login_ok or error (server replies immediately)
    try:
        reply = recv_json(_sock)
    except Exception as e:
        _safe_close_socket()
        _set_status("error", f"Failed to read login reply: {e}")
        return False

    if reply is None:
        _safe_close_socket()
        _set_status("error", "Server closed connection during login")
        return False

    if reply.get("type") == MSG_ERROR:
        _safe_close_socket()
        _set_status("error", reply.get("message", "Login rejected"))
        return False

    if reply.get("type") != MSG_LOGIN_OK:
        _safe_close_socket()
        _set_status("error", f"Unexpected login reply: {reply}")
        return False

    # Mark connected
    with _state_lock:
        _is_connected = True

    _set_status("connected", f"Logged in as {reply.get('username', username)}")

    # Start receiver thread
    _receiver_thread = threading.Thread(target=receive_loop, daemon=True)
    _receiver_thread.start()

    return True


def receive_loop():
    """
    Continuously receives messages from the server in a background thread.
    Calls the on_message callback for each received message.
    """
    global _is_connected

    while not _stop_event.is_set():
        try:
            msg = recv_json(_sock)
        except Exception as e:
            _set_status("error", f"Receive error: {e}")
            msg = None

        if msg is None:
            # Disconnected (or error)
            break

        if _on_message:
            try:
                _on_message(msg)
            except Exception:
                # Never let callback issues kill receiver thread
                pass

    with _state_lock:
        _is_connected = False

    _safe_close_socket()
    _set_status("disconnected", "Connection closed")


def send_group_message(text):
    """
    Sends a group chat message to the server.
    """
    if not is_connected():
        _set_status("error", "Not connected")
        return False

    try:
        send_json(_sock, {
            "type": MSG_GROUP,
            "text": text,
            "ts": current_timestamp()
        })
        return True
    except Exception as e:
        _set_status("error", f"Failed to send group message: {e}")
        return False


def send_private_message(target, text):
    """
    Sends a private message to a specific user via the server.
    """
    if not is_connected():
        _set_status("error", "Not connected")
        return False

    try:
        send_json(_sock, {
            "type": MSG_PRIVATE,
            "target": target,
            "text": text,
            "ts": current_timestamp()
        })
        return True
    except Exception as e:
        _set_status("error", f"Failed to send private message: {e}")
        return False


def disconnect():
    """
    Disconnects gracefully from the server.
    """
    global _is_connected
    _stop_event.set()

    with _state_lock:
        _is_connected = False

    _safe_close_socket()
    _set_status("disconnected", "Disconnected by user")


def is_connected():
    """
    Returns True if the client is currently connected.
    """
    with _state_lock:
        return bool(_is_connected)
