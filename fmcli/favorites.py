# favorites.py
import json
import os
from console_manager import console
from rich.table import Table

FAV_FILE = "favorites.json"

# ------------------ Helper Functions ------------------
def load_favorites():
    if not os.path.exists(FAV_FILE):
        return []
    with open(FAV_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_favorites(favorites):
    with open(FAV_FILE, "w") as f:
        json.dump(favorites, f, indent=2)

# ------------------ Favorite Operations ------------------
def add_favorite(station):
    favorites = load_favorites()
    # Avoid duplicates (match name + location)
    if any(f["name"] == station["name"] and f.get("location") == station.get("location") for f in favorites):
        console.print("[yellow]⭐ Station already in favorites.[/]")
        return
    favorites.append({
        "name": station["name"],
        "location": station.get("location", "N/A"),
        "genre": station.get("genre", "N/A"),
        "description": station.get("description", "")
    })
    save_favorites(favorites)
    console.print("[green]✅ Station added to favorites.[/]")

def remove_favorite(index):
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        removed = favorites.pop(index)
        save_favorites(favorites)
        console.print(f"[red]❌ Removed {removed['name']} from favorites.[/]")
    else:
        console.print("[red]❌ Invalid favorite index.[/]")

def show_favorites():
    favorites = load_favorites()
    if not favorites:
        console.print("[yellow]📜 No favorites saved.[/]")
        return []

    table = Table(title="⭐ Favorite Stations", header_style="bold magenta")
    table.add_column("No.", justify="center")
    table.add_column("Station", style="bold cyan")
    table.add_column("Location", style="green")
    table.add_column("Genre", style="magenta")

    for i, station in enumerate(favorites, 1):
        table.add_row(str(i), station["name"], station.get("location", "N/A"), station.get("genre", "N/A"))

    console.print(table)
    return favorites
