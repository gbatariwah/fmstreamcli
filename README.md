# 🎧 FMStream CLI

**FMStream CLI** is a lightweight command-line tool for streaming, searching, and managing your favorite online radio stations — all from your terminal from [fmstream]https://fmstream.org).

---

## 🚀 Features

* 🔎 **Search** for radio stations by name, genre or country
* 🎵 **Play** live streams directly via CLI
* ❤️ **Save** and manage favorite stations
* 🕒 **View playback history**
* 🧭 **Simple keyboard navigation** (play, pause, stop, back)

---

## 🧰 Requirements

* Python 3.10 or newer
* `ffplay` (from [FFmpeg](https://ffmpeg.org/download.html)) installed and available in PATH
* Terminal with UTF-8 and Rich text color support

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/gbatariwah/fmstreamcli.git
   cd fmstreamcli
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate     # (On Windows: .\.venv\Scripts\activate)
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Usage

Run the main entry script:

```bash
python main.py
```

### Keyboard shortcuts

| Key   | Action           |
| ----- | ---------------- |
| **s** | Search stations  |
| **f** | Favorites        |
| **h** | Playback history |
| **p** | Play/Pause       |
| **x** | Stop playback    |
| **q** | Quit application |

---

## 📁 Project Structure

```
radio_cli/
├── .venv/                # Virtual environment (not tracked)
└── fmcli/
    ├── main.py           # CLI entry point
    ├── search.py         # Station search logic
    ├── player.py         # Stream player controls
    ├── favorites.py      # Favorites management
    ├── history.py        # Playback history tracking
    └── utils.py          # Helper utilities
```

---

## 🧾 License

This project is licensed under the [MIT License](LICENSE).

---

## 💡 Future Improvements

* Add volume control
* Add station categories
* Add asynchronous playback with better error handling

---

### Author

**Gerald Batariwah**
🔗 [github.com/gbatariwah](https://github.com/gbatariwah)
