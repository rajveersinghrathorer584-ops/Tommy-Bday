# 🎂 Happy Birthday, Tommy! 💗

A birthday surprise built with Python and Streamlit. Every visual is made with
CSS, HTML, typography and emoji: there are no photos, image files or image APIs.

## What's inside

| Chapter | What happens |
| --- | --- |
| **Welcome** | Animated balloons, a glowing CSS cake and a greeting card. **Open Your Surprise 🎁** sets off confetti. |
| **1 · Make a Wish** | A three-tier cake with flickering candles. **Make a Wish** blows them out (with smoke), shows a wish message and sends hearts floating up. |
| **2 · A Letter For You** | A sealed envelope that unfolds into a letter on stationery. |
| **3 · A Secret Gift** | A gift box that wiggles. Opening it lifts the lid, sends out light rays and sparkles, and shows a secret message, then a second surprise. |
| **4 · Little Wishes** | Every click shows a new random wish (sweet, funny, heartfelt, blessing or cute) on an animated card. |
| **5 · Counting the Moments** | A live countdown in days, hours, minutes and seconds. On her birthday it shows a celebration message instead. |
| **6 · The Grand Finale** | A night sky with looping fireworks, a final message, **Celebrate Again 🎉**, and an optional music player. |

## Setup (Windows PowerShell)

Open PowerShell in this `birthday_dashboard` folder, then run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>.

> If PowerShell says running scripts is disabled, run this once and then activate again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Personalize it (`config.py`)

Everything she sees is set in [`config.py`](config.py). Save the file and refresh the browser.

| Setting | What it controls |
| --- | --- |
| `SISTER_NAME` | Her nickname (`"Tommy"`) |
| `YOUR_NAME` | **Replace the placeholder.** It signs the letter, the welcome card and the footer. |
| `BIRTHDAY` | **Replace the placeholder.** Use `"MM-DD"` (e.g. `"08-14"`) or `"YYYY-MM-DD"`. With a year, the countdown also shows the age she's turning. |
| `LEAP_DAY_CELEBRATION` | For a 29 February birthday in non-leap years: `"02-28"` or `"03-01"` |
| `LETTER_GREETING`, `LETTER_BODY`, `LETTER_SIGNOFF` | The letter. Leave a blank line between paragraphs. |
| `SECRET_GIFT_*`, `SECOND_SURPRISE_*` | The two messages inside the gift |
| `BIRTHDAY_WISHES` | Wishes grouped by category. Add, remove or rename freely. |
| `WISH_MESSAGE`, `WELCOME_*`, `FINAL_*` | Text for the welcome screen, the cake and the finale |
| `THEME` | Colours (pink, lavender, cream, peach, gold, text) |
| `AUDIO_FILE` | Optional song (see below) |

Until `BIRTHDAY` holds a real date, the countdown shows a short reminder instead of failing.

### Music

Two versions of "Happy Birthday to You" (a public-domain melody) are included, both synthesized for this project:

- `assets/birthday_song_meow.wav` (**the one that plays**): a cat sings the tune, one meow
  per note, over soft music-box chords. In the second verse a tiny kitten meows back. About 40 seconds.
- `assets/birthday_song.wav`: a gentle music-box version without the cat, about 41 seconds.

The song plays on a loop from a mini player pinned to the bottom of the screen, which
she can pause at any time. It starts as soon as the page opens. If her browser blocks
sound until she interacts with the page, it starts on her first click instead (usually
**Open Your Surprise 🎁**). Once paused, it stays paused.

To use a different song, put it in `assets/` (mp3, wav and ogg all work) and update
`AUDIO_FILE` in `config.py` to match.

A player appears in the finale. It never autoplays. Without a file, the player stays hidden.

## Project structure

```
birthday_dashboard/
├── app.py              # page layout, chapters, and button callbacks
├── config.py           # all personal text, the date and the colours
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml     # keeps the pastel light theme even in dark mode
└── utils/
    ├── __init__.py
    └── helpers.py      # CSS, cake/gift/fireworks markup, date logic, countdown
```

## How it works

- **No extra reruns.** Buttons update `st.session_state` through `on_click` callbacks, so each click causes exactly one rerun. Everything stays open as she scrolls: blown candles, the open letter, the unwrapped gift and the current wish.
- **Animations don't replay by accident.** Celebration effects are tied to a counter, so they play once per click and stay put when anything else on the page changes. Each chapter sits in its own container, so opening one doesn't re-animate the others.
- **The countdown runs in the browser.** It ticks every second with a little JavaScript, without reloading the app.
- **Dates are validated.** Impossible dates (e.g. `"02-30"`), leap-day birthdays and birthdays already past this year are all handled.
- **Responsive and gentle.** The layout adapts to phones, and animations are toned down for anyone who has "reduce motion" turned on.

The fonts (Great Vibes, Dancing Script, Quicksand and Cormorant Garamond) load from Google Fonts. Offline, the page falls back to system fonts and still works.
