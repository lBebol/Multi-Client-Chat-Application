import socket
import threading

from common import (
    send_json,
    recv_json,
    current_timestamp,
    MSG_LOGIN,
    MSG_LOGIN_OK,
    MSG_GROUP,
    MSG_PRIVATE,
    MSG_SYSTEM,
    MSG_ERROR,
    MSG_HISTORY_RESPONSE,
)

from storage import (
    save_message,
    load_group_history,
    load_private_history,
)

# =========================
# Server state
# =========================

clients = {}        
usernames = {}      
lock = threading.Lock()


# =========================
# Client handling
# =========================

def handle_client(client_socket):
    username = None

    try:
        # ---- LOGIN ----
        msg = recv_json(client_socket)
        if not msg or msg.get("type") != MSG_LOGIN:
            send_json(client_socket, {
                "type": MSG_ERROR,
                "message": "Login required"
            })
            return

        username = msg.get("username")

        with lock:
            if username in usernames:
                send_json(client_socket, {
                    "type": MSG_ERROR,
                    "message": "Username already taken"
                })
                return

            clients[client_socket] = username
            usernames[username] = client_socket

        send_json(client_socket, {
            "type": MSG_LOGIN_OK,
            "username": username
        })

        # ---- SEND HISTORY ----
        send_history(client_socket, username)

        broadcast_system(f"{username} joined the chat")

        # ---- MAIN LOOP ----
        while True:
            msg = recv_json(client_socket)
            if msg is None:
                break

            msg_type = msg.get("type")

            if msg_type == MSG_GROUP:
                handle_group_message(username, msg)

            elif msg_type == MSG_PRIVATE:
                handle_private_message(username, msg)

    except Exception as e:
        print(f"[Server Error] {e}")

    finally:
        remove_client(client_socket)


# =========================
# Message handlers
# =========================

def handle_group_message(sender, msg):
    text = msg.get("text")
    ts = current_timestamp()

    save_message(ts, sender, "group", None, text)

    message = {
        "type": MSG_GROUP,
        "from": sender,
        "text": text,
        "ts": ts
    }

    with lock:
        for sock in clients:
            send_json(sock, message)


def handle_private_message(sender, msg):
    target = msg.get("target")
    text = msg.get("text")
    ts = current_timestamp()

    save_message(ts, sender, "pm", target, text)

    message = {
        "type": MSG_PRIVATE,
        "from": sender,
        "target": target,
        "text": text,
        "ts": ts
    }

    with lock:
        target_sock = usernames.get(target)
        sender_sock = usernames.get(sender)

    if target_sock:
        send_json(target_sock, message)
    if sender_sock:
        send_json(sender_sock, message)


def broadcast_system(text):
    message = {
        "type": MSG_SYSTEM,
        "text": text,
        "ts": current_timestamp()
    }

    with lock:
        for sock in clients:
            send_json(sock, message)


# =========================
# History handling
# =========================

def send_history(sock, username):
    group_history = load_group_history(limit=50)

    send_json(sock, {
        "type": MSG_HISTORY_RESPONSE,
        "scope": "group",
        "messages": group_history
    })

    with lock:
        for other in usernames:
            if other != username:
                pm_history = load_private_history(username, other, limit=50)
                if pm_history:
                    send_json(sock, {
                        "type": MSG_HISTORY_RESPONSE,
                        "scope": "pm",
                        "with": other,
                        "messages": pm_history
                    })


# =========================
# Cleanup
# =========================

def remove_client(client_socket):
    with lock:
        username = clients.pop(client_socket, None)
        if username:
            usernames.pop(username, None)

    if username:
        broadcast_system(f"{username} left the chat")

    client_socket.close()


# =========================
# Server startup
# =========================

def start_server(host="0.0.0.0", port=12345):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Server running on {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket,),
            daemon=True
        )
        thread.start()
