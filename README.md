# Multi-Client Chat Application

---

## Team Members
- Abdelrahman Zaky | 231000102
- Abdelrahman Abouzeid | 231001168
- Ibrahim Mohammed | 231000257
- Ahmed hatem Ahmed | 221001690

---

## Project Overview

This project is a multi-client chat application implemented using Python socket programming.  
It follows a **server–client architecture**, supports **group and private messaging**, stores messages for **persistence**, and works over **both wired and wireless local networks without internet access**.

The application is designed to be simple, reliable, and easy to understand.

---

## Folder Structure Overview

The project uses a minimal and clean structure to avoid over-engineering while still keeping responsibilities clearly separated.

```
multi-client-chat/
├── README.md
├── requirements.txt
├── common.py
├── server.py
├── storage.py
├── client_net.py
├── run_server.py
├── run_client_cli.py
└── data/
    └── chat.db
```

---

## File Descriptions and Responsibilities

---

## `common.py`

### Purpose
This file defines the **communication protocol** shared between the server and all clients.  
It contains message type constants and helper functions for sending and receiving JSON messages over sockets.

Keeping the protocol in one place ensures consistency and prevents mismatches between client and server.

### Functions

#### `send_json(sock, data)`
**Description:**  
Serializes a Python dictionary into JSON format, appends a newline character, and sends it over the socket.

**How it works:**  
- Converts `data` to a JSON string
- Adds `\n` as a message delimiter
- Sends the encoded string using the socket

---

#### `recv_json(sock)`
**Description:**  
Receives a single JSON message from a socket and converts it back into a Python dictionary.

**How it works:**  
- Reads data from the socket until a newline is found
- Decodes the bytes into a string
- Parses the JSON string into a dictionary
- Returns the parsed message

---

#### `current_timestamp()`
**Description:**  
Returns the current Unix timestamp.

**How it works:**  
- Uses the system clock
- Converts the time to an integer timestamp
- Used for message ordering and persistence

---

## `server.py`

### Purpose
This file implements the **chat server**.  
The server listens for incoming connections, creates a new thread for each client, routes messages, and manages connected users.

It is responsible for:
- Handling multiple clients simultaneously
- Broadcasting group messages
- Delivering private messages
- Detecting and handling disconnections

```
START SERVER
   |
   |-- listen on a port
   |
CLIENT CONNECTS
   |
   |-- start a new thread for this client
   |
CLIENT SENDS LOGIN
   |
   |-- register username
   |
CLIENT SENDS MESSAGE
   |
   |-- check message type
   |-- broadcast / route / store
   |
CLIENT DISCONNECTS
   |
   |-- remove client
   |-- notify others
```

### Functions

#### `start_server(host, port)`
**Description:**  
Starts the server socket and listens for incoming client connections.

**How it works:**  
- Creates a TCP socket
- Binds it to the specified host and port
- Listens for incoming connections
- Starts a new thread for each connected client

---

#### `handle_client(client_socket)`
**Description:**  
Handles all communication with a single connected client.

**How it works:**  
- Runs in its own thread
- Receives messages from the client
- Processes message types (login, group, private)
- Detects client disconnection and cleans up resources

---

#### `register_user(username, client_socket)`
**Description:**  
Registers a new user in the server’s in-memory data structures.

**How it works:**  
- Checks if the username already exists
- Maps username to socket and socket to username
- Returns success or failure

---

#### `broadcast_message(message, sender)`
**Description:**  
Sends a group message to all connected clients.

**How it works:**  
- Iterates over all connected client sockets
- Sends the message to each client except the sender (optional)
- Used for group chat and system notifications

---

#### `send_private_message(sender, target, message)`
**Description:**  
Sends a private message from one user to another.

**How it works:**  
- Looks up the target user’s socket
- Sends the message only to the target and optionally the sender
- Ensures privacy by not broadcasting the message

---

#### `remove_client(client_socket)`
**Description:**  
Removes a disconnected client from the server.

**How it works:**  
- Deletes the user from all tracking dictionaries
- Closes the socket
- Broadcasts a system message indicating the user left

---

## `storage.py`

### Purpose
This file handles **message persistence** using SQLite.  
It allows messages to be stored and retrieved so users can see previous messages after reconnecting.

The database file is automatically created in the `data/` folder.

### Functions

#### `init_db()`
**Description:**  
Initializes the SQLite database and creates required tables.

**How it works:**  
- Connects to `data/chat.db`
- Creates the `messages` table if it does not exist
- Closes the connection

---

#### `save_message(timestamp, sender, scope, target, text)`
**Description:**  
Stores a chat message in the database.

**How it works:**  
- Inserts message data into the `messages` table
- Supports both group and private messages

---

#### `load_group_history(limit)`
**Description:**  
Retrieves recent group chat messages.

**How it works:**  
- Queries the database for group messages
- Orders messages by timestamp
- Returns the last `limit` messages

---

#### `load_private_history(user1, user2, limit)`
**Description:**  
Retrieves private message history between two users.

**How it works:**  
- Queries messages where sender and target match either user
- Orders messages by timestamp
- Returns the last `limit` messages

---

## `client_net.py`

### Purpose
This file implements the **client-side networking logic** without any graphical interface.  
It manages the socket connection, sending messages, and receiving messages in a background thread.

The GUI (added later) will communicate only with this module.

### Functions

#### `connect(server_ip, port, username)`
**Description:**  
Connects the client to the server and performs login.

**How it works:**  
- Opens a TCP connection to the server
- Sends a login message with the username
- Starts the receiver thread

---

#### `receive_loop()`
**Description:**  
Continuously listens for incoming messages from the server.

**How it works:**  
- Runs in a separate thread
- Calls `recv_json()` repeatedly
- Passes received messages to a callback or handler
- Detects disconnection events

---

#### `send_group_message(text)`
**Description:**  
Sends a group chat message to the server.

**How it works:**  
- Wraps the text in a group message format
- Sends it using `send_json()`

---

#### `send_private_message(target, text)`
**Description:**  
Sends a private message to a specific user.

**How it works:**  
- Creates a private message object
- Includes the target username
- Sends it to the server

---

#### `disconnect()`
**Description:**  
Closes the client connection gracefully.

**How it works:**  
- Closes the socket
- Stops the receiver thread
- Updates connection status

---

## `run_server.py`

### Purpose
This file serves as the **entry point** for starting the server.

### Functions

#### `main()`
**Description:**  
Starts the server application.

**How it works:**  
- Initializes the database
- Calls `start_server()` with configuration values
- Keeps the server running until manually stopped

---

## `run_client_cli.py`

### Purpose
This file provides a **simple command-line client** used for testing the system before the GUI is implemented.

### Functions

#### `main()`
**Description:**  
Starts a terminal-based client session.

**How it works:**  
- Prompts the user for server details and username
- Connects to the server
- Reads user input from the terminal
- Sends messages to the server
- Prints received messages to the console

---

## Notes

- The `data/chat.db` file is automatically created when the server starts.
- The application works over local wired or wireless networks without internet access.
- A graphical user interface using `tkinter` will be added after the networking backend is complete.

---
