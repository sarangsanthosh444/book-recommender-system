import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from io import BytesIO

import requests
from PIL import Image, ImageTk

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{}-M.jpg"
HEADERS = {"User-Agent": "BookRecommenderStudentProject/1.0"}

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "Images")

BLUE = "#0096FF"
DARK = "#0d0d1a"
GREEN = "#0b7a5a"
COVER_SIZE = (130, 180)
FONT = "Helvetica"


def load_icon(name, size):
    """Load an image from the Images folder, or return None if missing."""
    try:
        img = Image.open(os.path.join(IMG_DIR, name)).convert("RGBA")
        return ImageTk.PhotoImage(img.resize(size))
    except Exception:
        return None


class BookApp:
    def __init__(self, root):
        self.root = root
        self.max_results = 5
        self.photos = []
        self.q = queue.Queue()

        root.title("Book Recommender System")
        root.geometry("1000x620")
        root.configure(bg=DARK)

        self.logo = load_icon("logo.png", (70, 70))
        self.book_icon = load_icon("icon.png", (70, 45))
        self.search_icon = load_icon("Search.png", (22, 22))
        self.setting_icon = load_icon("setting.png", (30, 30))
        self.logout_icon = load_icon("logout.png", (30, 30))

        self.build_header()

        self.holder = tk.Frame(root, bg=DARK)
        self.holder.pack(expand=True)

        self.status = tk.Label(root, text="Type a book name and press Search",
                               bg=DARK, fg="white", font=(FONT, 12))
        self.status.pack(side="bottom", pady=8)

        self.poll()

    def build_header(self):
        header = tk.Frame(self.root, bg=BLUE, height=210)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Button(header, image=self.logout_icon,
                  text="" if self.logout_icon else "Logout",
                  command=self.logout, highlightbackground=BLUE
                  ).place(relx=0.96, y=15, anchor="ne")

        title_row = tk.Frame(header, bg=BLUE)
        title_row.pack(pady=(35, 12))
        if self.logo:
            tk.Label(title_row, image=self.logo, bg=BLUE).pack(side="left", padx=10)
        tk.Label(title_row, text="BOOK RECOMMENDATION", bg=BLUE, fg="white",
                 font=(FONT, 26, "bold")).pack(side="left")

        bar = tk.Frame(header, bg=BLUE)
        bar.pack()
        if self.book_icon:
            tk.Label(bar, image=self.book_icon, bg=BLUE).pack(side="left", padx=(0, 4))

        self.entry = tk.Entry(bar, width=30, font=(FONT, 18), relief="flat",
                              bg="white", fg="black", insertbackground="black",
                              highlightthickness=0)
        self.entry.pack(side="left", ipady=7)
        self.entry.bind("<Return>", lambda e: self.search())
        self.entry.focus()

        search_btn = tk.Label(bar, text=" Search ", image=self.search_icon,
                              compound="left", bg=GREEN, fg="white",
                              font=(FONT, 13, "bold"), padx=15, pady=9,
                              cursor="hand2")
        search_btn.pack(side="left", padx=(0, 15))
        search_btn.bind("<Button-1>", lambda e: self.search())

        tk.Button(bar, image=self.setting_icon,
                  text="" if self.setting_icon else "⚙",
                  command=self.open_settings, highlightbackground=BLUE,
                  font=(FONT, 16)).pack(side="left")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("300x160")
        win.configure(bg="white")
        win.transient(self.root)

        tk.Label(win, text="Number of results (1-5):", bg="white", fg="black",
                 font=(FONT, 12)).pack(pady=(20, 5))
        spin = tk.Spinbox(win, from_=1, to=5, width=5, font=(FONT, 12))
        spin.delete(0, "end")
        spin.insert(0, self.max_results)
        spin.pack()

        def save():
            try:
                self.max_results = max(1, min(5, int(spin.get())))
            except ValueError:
                pass
            win.destroy()

        tk.Button(win, text="Save", command=save).pack(pady=15)

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to exit?"):
            self.root.destroy()

    def search(self):
        query = self.entry.get().strip()
        if not query:
            return
        self.status.config(text="Searching...")
        threading.Thread(target=self.fetch, args=(query, self.max_results),
                         daemon=True).start()

    def fetch(self, query, count):
        try:
            r = requests.get(
                SEARCH_URL,
                params={"q": query, "limit": count,
                        "fields": "title,first_publish_year,cover_i,ratings_average"},
                headers=HEADERS, timeout=15)
            r.raise_for_status()

            books = []
            for doc in r.json().get("docs", []):
                img = None
                cover_id = doc.get("cover_i")
                if cover_id:
                    try:
                        data = requests.get(COVER_URL.format(cover_id),
                                            headers=HEADERS, timeout=15).content
                        img = Image.open(BytesIO(data)).convert("RGB")
                    except Exception:
                        img = None
                if img is None:
                    img = Image.new("RGB", COVER_SIZE, "#888888")

                rating = doc.get("ratings_average")
                books.append({
                    "title": doc.get("title", "No Title"),
                    "date": doc.get("first_publish_year", "N/A"),
                    "rating": round(rating, 1) if rating else "N/A",
                    "img": img.resize(COVER_SIZE),
                })
            self.q.put(("ok", books))
        except Exception as e:
            self.q.put(("err", e))

    def poll(self):
        """Check the queue every 100 ms (safe way to update the GUI)."""
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "ok":
                    self.show(data)
                else:
                    self.status.config(text=f"Error: {data}")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def show(self, books):
        for w in self.holder.winfo_children():
            w.destroy()
        self.photos.clear()

        if not books:
            self.status.config(text="No books found.")
            return
        self.status.config(text="")

        for book in books:
            card = tk.Frame(self.holder, bg="white", padx=6, pady=6)
            card.pack(side="left", padx=12)

            title = book["title"]
            if len(title) > 20:
                title = title[:18] + "..."
            tk.Label(card, text=title, bg="white", fg="green",
                     font=(FONT, 10)).pack(anchor="w")

            photo = ImageTk.PhotoImage(book["img"])
            self.photos.append(photo)
            tk.Label(card, image=photo, bg="white").pack()

            info = tk.Frame(card, bg="#e6e6e6")
            info.pack(fill="x", pady=(6, 0))
            tk.Label(info, text=f"Date: {book['date']}", bg="#e6e6e6",
                     fg="red", font=(FONT, 10)).pack(anchor="w")
            tk.Label(info, text=f"Rating: {book['rating']}", bg="#e6e6e6",
                     fg="black", font=(FONT, 10)).pack(anchor="w")


if __name__ == "__main__":
    root = tk.Tk()
    BookApp(root)
    root.mainloop()
