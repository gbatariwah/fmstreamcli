from rich.text import Text
from rich.style import Style
from rich.align import Align
from rich.panel import Panel


def get_logo_panel() -> Text:
    """
    Creates a Text object representing the FMCLI logo using large ASCII art
    and a custom gradient to mimic the pixelated style from the image.
    """
    # Define a larger ASCII art logo using block characters
    # '█' is a full block, '▓' is a heavy shade (used to simulate fading/pixellation)
    large_logo = r"""
  $$$$$$\                          $$\ $$\ 
$$  __$$\                         $$ |\__|
$$ /  \__|$$$$$$\$$$$\   $$$$$$$\ $$ |$$\ 
$$$$\     $$  _$$  _$$\ $$  _____|$$ |$$ |
$$  _|    $$ / $$ / $$ |$$ /      $$ |$$ |
$$ |      $$ | $$ | $$ |$$ |      $$ |$$ |
$$ |      $$ | $$ | $$ |\$$$$$$$\ $$ |$$ |
\__|      \__| \__| \__| \_______|\__|\__|                  
"""

    # 1. Create the base Text object
    logo_text = Text(large_logo, justify="center")

    # Define the single color (light pink)
    single_color = "rgb(255, 150, 255)"  # Light Pink

    # 2. Apply the single color to the entire logo text
    logo_text.stylize(Style(bold=True, color=single_color))

    # 3. Add the secondary title
    title_text = Text("\nFMStream CLI\n", style="bold white", justify="center")

    # 4. Combine and return
    combined_text = logo_text + title_text

    return combined_text