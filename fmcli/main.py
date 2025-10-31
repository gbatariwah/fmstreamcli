import sys
import time
from console_manager import console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.align import Align
from rich.text import Text
from utils import clear_console
from search import search_stations, show_station_list, show_streams
from player import play_stream_ffplay
from history import add_to_history, show_history
from favorites import add_favorite, remove_favorite, show_favorites
from logo import get_logo_panel


def main():
    global history
    history = []

    while True:
        clear_console()
        layout = get_logo_panel()
        console.print(layout)

        # Header
        header_text = Text("🎧 FMStream Radio CLI", style="bold magenta", justify="center")
        subtext = Text("(s) Search stations   (h) History   (f) Favorites   (q) Quit",
                       style="bold cyan", justify="center")
        full_text = Text.assemble(header_text, "\n", subtext)

        console.print(
            Panel(
                Align.center(full_text),
                border_style="bright_magenta",
                padding=(1, 4),
                title="[bold yellow]🎵 Welcome![/]",
                expand=False
            )
        )

        action = Prompt.ask("[bold green]Choose an action[/]").strip().lower()

        # --- Quit ---
        if action == "q":
            console.print("[yellow]👋 Exiting player.[/]")
            break

        # --- Search Stations ---
        elif action == "s":
            query = Prompt.ask("[bold green]Enter station name (b=back)[/]").strip()
            if query.lower() == "b":
                continue

            start_index = 0
            while True:
                results, prev_link, next_link = search_stations(query, start_index)
                if not results:
                    console.print("[red]❌ No stations found.[/]")
                    time.sleep(2)
                    break

                show_station_list(results)
                options = "[bold cyan]Select a station number[/] (b=back)"
                if prev_link is not None:
                    options += " (p) Previous"
                if next_link is not None:
                    options += " (n) Next"
                choice = Prompt.ask(options).strip().lower()

                if choice == "b":
                    break
                if choice == "p" and prev_link is not None:
                    start_index = prev_link
                    continue
                if choice == "n" and next_link is not None:
                    start_index = next_link
                    continue
                if not choice.isdigit() or not (1 <= int(choice) <= len(results)):
                    console.print("[red]❌ Invalid choice.[/]")
                    time.sleep(1)
                    continue

                station = results[int(choice) - 1]

                while True:
                    show_streams(station)
                    stream_choice = Prompt.ask(
                        "[bold cyan]Select stream number to play (b=back, a=add to favorites)[/]"
                    ).strip().lower()

                    if stream_choice == "b":
                        break
                    if stream_choice == "a":
                        add_favorite(station)
                        continue
                    if not stream_choice.isdigit() or not (1 <= int(stream_choice) <= len(station["streams"])):
                        console.print("[red]❌ Invalid stream choice.[/]")
                        time.sleep(1)
                        continue

                    # Get selected stream
                    stream = station["streams"][int(stream_choice) - 1]
                    stream.update({
                        "station_name": station["name"],
                        "station_genre": station["genre"],
                        "station_location": station["location"],
                        "station_description": station["description"],
                    })

                    # Add to history and auto-play
                    add_to_history(station, stream)
                    console.print(f"[bold yellow]🎵 Now playing: {stream['station_name']}[/]")
                    play_stream_ffplay(stream)
                    console.print("[cyan]↩️ Returning to station list...[/]")
                    time.sleep(1)
                    break

        # --- History ---
        elif action == "h":
            show_history()
            Prompt.ask("[dim]Press Enter to go back[/]")

        # --- Favorites ---
        elif action == "f":
            while True:
                favorites = show_favorites()
                if not favorites:
                    Prompt.ask("[dim]Press Enter to go back[/]")
                    break

                choice = Prompt.ask("[bold cyan]Select favorite station (b=back, r=remove)[/]").strip().lower()
                if choice == "b":
                    break
                if choice == "r":
                    remove_idx = Prompt.ask("[bold cyan]Enter number to remove[/]").strip()
                    if remove_idx.isdigit() and 1 <= int(remove_idx) <= len(favorites):
                        remove_favorite(int(remove_idx) - 1)
                    else:
                        console.print("[red]❌ Invalid number.[/]")
                    continue

                if choice.isdigit() and 1 <= int(choice) <= len(favorites):
                    station = favorites[int(choice) - 1]
                    results, _, _ = search_stations(station["name"])
                    if not results:
                        console.print("[red]❌ Could not fetch live streams.[/]")
                        continue

                    live_station = results[0]
                    show_streams(live_station)
                    stream_choice = Prompt.ask("[bold cyan]Select stream to play (b=back)[/]").strip().lower()
                    if stream_choice == "b":
                        continue
                    if stream_choice.isdigit() and 1 <= int(stream_choice) <= len(live_station["streams"]):
                        stream = live_station["streams"][int(stream_choice) - 1]
                        stream.update({
                            "station_name": live_station["name"],
                            "station_genre": live_station["genre"],
                            "station_location": live_station["location"],
                            "station_description": live_station["description"],
                        })
                        add_to_history(live_station, stream)
                        console.print(f"[bold yellow]🎵 Now playing: {stream['station_name']}[/]")
                        play_stream_ffplay(stream)
                        console.print("[cyan]↩️ Returning to favorites...[/]")
                        time.sleep(1)
        else:
            console.print("[red]❌ Invalid option.[/]")
            time.sleep(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
