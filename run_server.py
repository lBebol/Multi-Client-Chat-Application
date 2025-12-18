from server import start_server
from storage import init_db

def main():
    init_db()
    start_server(host="0.0.0.0", port=12345)

if __name__ == "__main__":
    main()
