# Book Recommender System

A desktop book-search and recommendation interface built with Python and Tkinter. It retrieves book information and cover images from the Open Library API and displays up to five results.

## Features

- Search for books by title or keyword
- Display book covers, first publication year, and average rating
- Configure the number of results (1–5)
- Fetch results on a background thread so the interface remains responsive
- Graceful fallback when a cover image is unavailable

## Tech stack

- Python and Tkinter
- Open Library Search API and Covers API
- Requests and Pillow
- Threading and Queue

## Setup

Requires Python 3.9 or newer and an internet connection.

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies and run:
```bash
pip install -r requirements.txt
python main.py
```

Tkinter is included with most standard Python installations; some Linux distributions require installing it separately.

## Optional icons

Place any available icons in the `Images/` directory next to `main.py`: `logo.png`, `icon.png`, `Search.png`, `setting.png`, and `logout.png`. The app uses text/button fallbacks when these files are missing.

## Screenshots

The three application screenshots supplied with the project are not yet present in this repository.

## APIs

- [Open Library Search API](https://openlibrary.org/dev/docs/api/search)
- [Open Library Covers API](https://openlibrary.org/dev/docs/api/covers)
