# run_client_gui.py
import tkinter as tk
from client_gui import ChatGUI

def main():
    root = tk.Tk()
    ChatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
