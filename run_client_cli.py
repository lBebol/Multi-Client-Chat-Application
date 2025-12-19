import sys
import client_net

from common import (
    MSG_SYSTEM,
    MSG_GROUP,
    MSG_PRIVATE,
    MSG_ERROR,
    MSG_HISTORY_RESPONSE,
    MSG_LOGIN_OK,
)

def _format_history_item(item):
    """
    Tries to format history rows safely even if storage returns dicts or tuples.
    Expected dict keys (recommended): ts, sender, scope, target, text
    """
    # Dict format
    if isinstance(item, dict):
        ts = item.get("ts", "")
        sender = item.get("sender", item.get("from", ""))
        scope = item.get("scope", "")
        target = item.get("target", "")
        text = item.get("text", "")
        if scope == "pm":
            return f"[PM] {sender} -> {target}: {text}"
        return f"{sender}: {text}"

    # Tuple/list format (fallback)
    if isinstance(item, (tuple, list)):
        # Try common patterns: (ts, sender, scope, target, text)
        if len(item) >= 5:
            _, sender, scope, target, text = item[:5]
            if scope == "pm":
                return f"[PM] {sender} -> {target}: {text}"
            return f"{sender}: {text}"
        # If unknown shape, just print it
        return str(item)

    return str(item)


def on_status(status, details=""):
    if status == "connected":
        print(f"\n[Connected] {details}\n")
    elif status == "disconnected":
        print(f"\n[Disconnected] {details}\n")
    elif status == "error":
        print(f"\n[Error] {details}\n")
    else:
        print(f"\n[{status}] {details}\n")


def on_message(msg):
    msg_type = msg.get("type")

    if msg_type == MSG_SYSTEM:
        print(f"\n* {msg.get('text', '')} *")
        return

    if msg_type == MSG_GROUP:
        sender = msg.get("from", "")
        text = msg.get("text", "")
        print(f"\n{sender}: {text}")
        return

    if msg_type == MSG_PRIVATE:
        sender = msg.get("from", "")
        target = msg.get("target", "")
        text = msg.get("text", "")
        print(f"\n[PM] {sender} -> {target}: {text}")
        return

    if msg_type == MSG_HISTORY_RESPONSE:
        scope = msg.get("scope")
        messages = msg.get("messages", [])

        if scope == "group":
            print("\n--- Group History ---")
            for item in messages:
                print(_format_history_item(item))
            print("--- End Group History ---\n")
            return

        if scope == "pm":
            other = msg.get("with", "unknown")
            print(f"\n--- PM History with {other} ---")
            for item in messages:
                print(_format_history_item(item))
            print(f"--- End PM History with {other} ---\n")
            return

        print(f"\n[History] {msg}")
        return

    if msg_type == MSG_LOGIN_OK:
        print(f"\n[Logged in as {msg.get('username', '')}]")
        return

    if msg_type == MSG_ERROR:
        print(f"\n[Server Error] {msg.get('message', '')}")
        return

    print(f"\n[Unknown message] {msg}")


def main():
    print("=== Multi-Client Chat (CLI) ===")
    server_ip = input("Server IP (e.g. 127.0.0.1): ").strip()
    port = input("Port (e.g. 12345): ").strip()
    username = input("Username: ").strip()

    ok = client_net.connect(
        server_ip=server_ip,
        port=int(port),
        username=username,
        on_message=on_message,
        on_status=on_status
    )

    if not ok:
        print("Failed to connect. Exiting.")
        return

    print("Type a group message and press Enter.")
    print("Private message format: /pm <username> <message>")
    print("Exit: Ctrl+C\n")

    try:
        while True:
            text = input()
            if not text:
                continue

            if text.startswith("/pm "):
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: /pm <username> <message>")
                    continue
                target = parts[1].strip()
                msg_text = parts[2].strip()
                client_net.send_private_message(target, msg_text)
            else:
                client_net.send_group_message(text)

    except KeyboardInterrupt:
        print("\nExiting...")
        client_net.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    main()
