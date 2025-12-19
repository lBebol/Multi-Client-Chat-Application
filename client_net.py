# abouzeid
from client_net import ClientNet

def on_message(msg):
    msg_type = msg.get("type")

    if msg_type == "group_message":
        print(f"[GROUP] {msg['from']}: {msg['text']}")

    elif msg_type == "private_message":
        print(f"[PRIVATE] {msg['from']}: {msg['text']}")

    elif msg_type == "system":
        print(f"[SYSTEM] {msg['text']}")

    else:
        print("[UNKNOWN]", msg)

def on_disconnect():
    print("Disconnected from server.")

def main():
    server_ip = input("Server IP: ").strip()
    port = int(input("Port: ").strip())
    username = input("Username: ").strip()

    client = ClientNet(
        on_message=on_message,
        on_disconnect=on_disconnect
    )

    client.connect(server_ip, port, username)
    print("Connected. Type messages below.")
    print("Use /pm username message for private chat")
    print("Use /quit to exit")

    try:
        while True:
            text = input()

            if text.lower() == "/quit":
                break

            if text.startswith("/pm "):
                _, target, *msg = text.split()
                client.send_private_message(target, " ".join(msg))
            else:
                client.send_group_message(text)

    except KeyboardInterrupt:
        pass

    finally:
        client.disconnect()
        print("Client closed.")

if __name__ == "__main__":
    main()
