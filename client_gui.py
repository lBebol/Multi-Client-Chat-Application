import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import client_net
from common import MSG_SYSTEM, MSG_GROUP, MSG_PRIVATE, MSG_HISTORY_RESPONSE

class ChatGUIAdvanced:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Multi-Client Chat")
        self.root.geometry("800x500")
        self.root.configure(bg="#1e1e1e")

        self.username = None
        self.online_users = set()

        self._build_login_screen()

    # =========================
    # Login Screen
    # =========================
    def _build_login_screen(self):
        self.login_frame = ttk.Frame(self.root, padding=20)
        self.login_frame.pack(fill="both", expand=True)

        ttk.Label(self.login_frame, text="Server IP").grid(row=0, column=0, sticky="w")
        ttk.Label(self.login_frame, text="Port").grid(row=1, column=0, sticky="w")
        ttk.Label(self.login_frame, text="Username").grid(row=2, column=0, sticky="w")

        self.ip_entry = ttk.Entry(self.login_frame)
        self.port_entry = ttk.Entry(self.login_frame)
        self.user_entry = ttk.Entry(self.login_frame)

        self.ip_entry.insert(0, "127.0.0.1")
        self.port_entry.insert(0, "12345")

        self.ip_entry.grid(row=0, column=1, pady=5)
        self.port_entry.grid(row=1, column=1, pady=5)
        self.user_entry.grid(row=2, column=1, pady=5)

        ttk.Button(self.login_frame, text="Connect", command=self._connect).grid(row=3, column=0, columnspan=2, pady=10)

    def _connect(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.user_entry.get().strip()

        if not ip or not port or not username:
            messagebox.showerror("Error", "All fields are required")
            return

        ok = client_net.connect(
            server_ip=ip,
            port=int(port),
            username=username,
            on_message=self._on_message,
            on_status=self._on_status
        )

        if not ok:
            return

        self.username = username
        self.login_frame.destroy()
        self._build_chat_screen()

    # =========================
    # Chat Screen
    # =========================
    def _build_chat_screen(self):
        self.chat_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Sidebar for online users
        sidebar = tk.Frame(self.chat_frame, width=150, bg="#2a2a2a")
        sidebar.pack(side="right", fill="y")
        tk.Label(sidebar, text="Online Users", bg="#2a2a2a", fg="#eaeaea").pack(pady=5)
        self.user_listbox = tk.Listbox(sidebar, bg="#1e1e1e", fg="#eaeaea", selectbackground="#4f9cff")
        self.user_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            state="disabled",
            wrap="word",
            bg="#1e1e1e",
            fg="#eaeaea",
            insertbackground="#eaeaea"
        )
        self.chat_display.pack(fill="both", expand=True, side="left", padx=5, pady=5)

        # Bottom input
        bottom = tk.Frame(self.root, bg="#1e1e1e")
        bottom.pack(fill="x", pady=5)

        self.mode_var = tk.StringVar(value="Group Chat")
        self.mode_dropdown = ttk.Combobox(
            bottom, textvariable=self.mode_var, state="readonly",
            values=["Group Chat", "Private Message"], width=16
        )
        self.mode_dropdown.pack(side="left", padx=5)

        self.msg_entry = tk.Entry(bottom, bg="#2a2a2a", fg="#eaeaea", insertbackground="#eaeaea", relief="flat")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        tk.Button(bottom, text="Send", bg="#3a3a3a", fg="#eaeaea", relief="flat", command=self._send_message).pack(side="right", padx=5)

        # Disconnect button
        tk.Button(bottom, text="Disconnect", bg="#3a3a3a", fg="#eaeaea", relief="flat", command=self._disconnect).pack(side="right", padx=5)

    # =========================
    # Sending Messages
    # =========================
    def _send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return

        mode = self.mode_var.get()
        if mode == "Group Chat":
            client_net.send_group_message(text)
        else:
            self._open_private_popup(text)

        self.msg_entry.delete(0, tk.END)

    def _open_private_popup(self, text):
        users = sorted(u for u in self.online_users if u != self.username)
        if not users:
            messagebox.showinfo("Private Message", "No other users online")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Select User")
        popup.configure(bg="#1e1e1e")
        popup.geometry("250x300")

        tk.Label(popup, text="Send private message to:", bg="#1e1e1e", fg="#eaeaea").pack(pady=10)

        listbox = tk.Listbox(popup, bg="#2a2a2a", fg="#eaeaea", selectbackground="#4f9cff")
        listbox.pack(fill="both", expand=True, padx=10, pady=5)
        for u in users:
            listbox.insert(tk.END, u)

        def send_pm():
            sel = listbox.curselection()
            if not sel:
                return
            target = listbox.get(sel[0])
            client_net.send_private_message(target, text)
            popup.destroy()

        tk.Button(popup, text="Send", bg="#3a3a3a", fg="#eaeaea", relief="flat", command=send_pm).pack(pady=10)

    # =========================
    # Receiving Messages
    # =========================
    def _on_message(self, msg):
        self.root.after(0, lambda: self._handle_message(msg))

    def _handle_message(self, msg):
        t = msg.get("type")

        if t == MSG_SYSTEM:
            text = msg.get("text", "")
            self._append_text(f"* {text} *\n")
            # Update online users
            if "joined the chat" in text:
                user = text.split(" joined the chat")[0].strip()
                self.online_users.add(user)
            if "left the chat" in text:
                user = text.split(" left the chat")[0].strip()
                self.online_users.discard(user)
            self._update_user_list()
            return

        if t == MSG_GROUP:
            sender = msg.get("from")
            self.online_users.add(sender)
            self._append_text(f"{sender}: {msg.get('text')}\n")
            self._update_user_list()
            return

        if t == MSG_PRIVATE:
            sender = msg.get("from")
            self.online_users.add(sender)
            self._append_text(f"[PM] {sender}: {msg.get('text')}\n")
            self._update_user_list()
            return

        if t == MSG_HISTORY_RESPONSE:
            scope = msg.get("scope")
            for item in msg.get("messages", []):
                sender = item.get("sender")
                text = item.get("text")
                if scope == "group":
                    self._append_text(f"{sender}: {text}\n")
                elif scope == "pm":
                    target = item.get("target")
                    self._append_text(f"[PM] {sender} -> {target}: {text}\n")
            self._append_text("\n")

    def _on_status(self, status, details):
        self.root.after(0, lambda: self._append_text(f"[{status}] {details}\n"))

    # =========================
    # Helpers
    # =========================
    def _append_text(self, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def _update_user_list(self):
        self.user_listbox.delete(0, tk.END)
        for u in sorted(self.online_users):
            self.user_listbox.insert(tk.END, u)

    def _disconnect(self):
        client_net.disconnect()
        self.root.destroy()


# =========================
# Run GUI
# =========================
def main():
    root = tk.Tk()
    ChatGUIAdvanced(root)
    root.mainloop()


if __name__ == "__main__":
    main()
