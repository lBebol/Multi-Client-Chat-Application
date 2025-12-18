import tkinter as tk

root = tk.Tk()
root.title("Network Project GUI")
root.geometry("400x300")

label = tk.Label(root, text="Welcome to Network Project", font=("Arial", 16))
label.pack(pady=20)

button = tk.Button(root, text="Click Me")
button.pack()

root.mainloop()