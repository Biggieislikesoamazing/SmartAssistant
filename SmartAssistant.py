import tkinter as tk
from tkinter import messagebox
import webbrowser
import platform
import os
import urllib.parse
import openai
import requests
import sys

# ==== SET YOUR OPENAI API KEY ====
openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your key

system = platform.system()

# ==== Detect Chrome path ====
def get_chrome_path():
    if system == "Windows":
        paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    elif system == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Linux":
        return "/usr/bin/google-chrome"
    return None

chrome_path = get_chrome_path()
if chrome_path:
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

# ==== Auto-detect installed apps (Windows) ====
def find_installed_apps():
    programs = {}
    paths_to_scan = [
        "C:/Program Files",
        "C:/Program Files (x86)",
        os.path.expandvars(r"C:/Users/%USERNAME%/AppData/Roaming")
    ]

    for base_path in paths_to_scan:
        for root_dir, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".exe"):
                    app_name = os.path.splitext(file)[0].lower()
                    full_path = os.path.join(root_dir, file)
                    programs[app_name] = full_path
    return programs

apps_paths = find_installed_apps()

# ==== Friendly name mapping for apps ====
friendly_names = {
    "spotify": "Spotify",
    "discord": "Discord",
    "steam": "Steam",
    "notepad": "notepad",
    "calculator": "calc"
}

# ==== Helper functions ====
def open_app(app_name):
    name_to_search = friendly_names.get(app_name.lower(), app_name.lower())
    path = apps_paths.get(name_to_search.lower())
    if path and os.path.exists(path):
        os.startfile(path)
    else:
        messagebox.showinfo("Info", f"App '{app_name}' not found. Opening search instead.")
        search_web(app_name)

def close_app(app_name):
    name_to_search = friendly_names.get(app_name.lower(), app_name.lower())
    if name_to_search.lower() in apps_paths.keys():
        if system == "Windows":
            os.system(f"taskkill /im {name_to_search}.exe /f")
        else:
            os.system(f"pkill {name_to_search}")
    else:
        messagebox.showinfo("Info", f"Cannot close '{app_name}'. Only real applications can be closed.")

def search_web(query):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    if chrome_path:
        webbrowser.get('chrome').open(url)
    else:
        webbrowser.open(url)

# ==== GPT command analysis ====
def analyze_command_gpt(command):
    prompt = f"""
You are a smart assistant. A user gives you a command.
Decide whether the command is to:
1. Open a website (YouTube, Google, Wikipedia, Maps)
2. Open a program/application installed on the computer
3. Close an application
4. Perform a Google search

Return a JSON object ONLY with keys:
- action: "open_url", "open_app", "close_app", or "search"
- target: the URL for websites OR app name to open/close OR search query

Command: "{command}"
"""
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0
        )
        import json
        data = json.loads(response.choices[0].text.strip())
        return data
    except Exception as e:
        print("Error contacting GPT:", e)
        return None

# ==== Handle commands ====
def handle_command():
    command = command_entry.get().lower()
    if not command:
        messagebox.showerror("Error", "Please type a command.")
        return

    # Check for installed apps first
    app_found = None
    for app_name, path in apps_paths.items():
        friendly_name = {v.lower(): k for k, v in friendly_names.items()}.get(app_name.lower(), app_name.lower())
        if friendly_name in command:
            app_found = app_name
            break

    if app_found:
        open_app(app_found)
    else:
        data = analyze_command_gpt(command)
        if not data:
            action, target = "search", command
        else:
            action = data.get("action")
            target = data.get("target")

        try:
            if action == "open_url":
                if chrome_path:
                    webbrowser.get('chrome').open(target)
                else:
                    webbrowser.open(target)
            elif action == "search":
                search_web(target)
            elif action == "open_app":
                open_app(target)
            elif action == "close_app":
                close_app(target)
            else:
                messagebox.showinfo("Info", "Command not recognized.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not execute command: {e}")

    command_entry.delete(0, tk.END)

# ==== Update button functionality ====
def update_app():
    # Replace this URL with your GitHub raw file URL
    url = "https://raw.githubusercontent.com/yourusername/SmartAssistant/main/assistant.py"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(sys.argv[0], "w", encoding="utf-8") as f:
                f.write(r.text)
            messagebox.showinfo("Update", "App updated successfully! Please restart the app.")
        else:
            messagebox.showerror("Update Error", f"Failed to fetch update. Status code: {r.status_code}")
    except Exception as e:
        messagebox.showerror("Update Error", f"Error updating app: {e}")

# ==== Tkinter GUI ====
root = tk.Tk()
root.title("Smart Assistant GPT")
root.geometry("700x350")
root.configure(bg="#2C2F33")
root.resizable(False, False)

frame = tk.Frame(root, bg="#2C2F33")
frame.pack(expand=True)

title_label = tk.Label(frame, text="💡 Smart Assistant GPT", font=("Helvetica", 20, "bold"), fg="#FFFFFF", bg="#2C2F33")
title_label.pack(pady=(10, 20))

entry_frame = tk.Frame(frame, bg="#23272A", bd=0)
entry_frame.pack(pady=(0, 20))
command_entry = tk.Entry(entry_frame, width=55, font=("Helvetica", 14), bd=0, fg="#FFFFFF", bg="#23272A", insertbackground="white")
command_entry.pack(ipady=8, padx=5)

def on_enter(e):
    go_button['bg'] = "#43B581"
def on_leave(e):
    go_button['bg'] = "#4CAF50"

go_button = tk.Button(frame, text="Go", command=handle_command, font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", bd=0, activebackground="#43B581", padx=20, pady=8)
go_button.pack()
go_button.bind("<Enter>", on_enter)
go_button.bind("<Leave>", on_leave)

# ==== Update Button ====
update_button = tk.Button(frame, text="Update App", command=update_app, font=("Helvetica", 12, "bold"), bg="#FF9800", fg="white", bd=0, padx=20, pady=8)
update_button.pack(pady=10)

command_entry.focus()
root.mainloop()
