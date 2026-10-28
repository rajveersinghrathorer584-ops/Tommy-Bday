"""Rendering, animation and date helpers for the birthday dashboard."""

from __future__ import annotations

import calendar
import html
import math
import random
import re
from datetime import date

import streamlit as st

# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "([\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿]"
    "[️‍\U0001F000-\U0001FAFF☀-➿]*)"
)


def flatten(markup: str) -> str:
    """Collapse markup onto one line so Markdown never turns it into a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def render(markup: str) -> None:
    st.markdown(flatten(markup), unsafe_allow_html=True)


def esc(text: str) -> str:
    return html.escape(str(text), quote=False)


def gradient_text(text: str) -> str:
    """Escape text and keep emojis in full colour inside gradient-clipped headings."""
    return _EMOJI_RE.sub(r'<span class="emoji">\1</span>', esc(text))


def paragraphs(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    return "".join(f"<p>{esc(b)}</p>" for b in blocks)


def shade(hex_color: str, factor: float) -> str:
    """Darken (factor < 1) or lighten (factor > 1) a #rrggbb colour."""
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    if factor < 1:
        r, g, b = (int(c * factor) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (factor - 1)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Birthday dates
# ---------------------------------------------------------------------------


def parse_birthday(value: str) -> tuple[int | None, int, int]:
    """Parse "MM-DD" or "YYYY-MM-DD" into (year | None, month, day).

    Raises ValueError with a readable message for anything invalid.
    """
    parts = str(value).strip().split("-")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValueError(f'"{value}" is not a date. Use "MM-DD" or "YYYY-MM-DD".')

    year = int(parts[0]) if len(parts) == 3 else None
    month, day = int(parts[-2]), int(parts[-1])

    if not 1 <= month <= 12:
        raise ValueError(f"Month {month} doesn't exist — it must be 1 to 12.")
    # 2000 is a leap year, so 29 February is accepted here.
    if not 1 <= day <= calendar.monthrange(2000, month)[1]:
        raise ValueError(f"Day {day} doesn't exist in {calendar.month_name[month]}.")
    if year is not None:
        if year < 1900 or year > date.today().year:
            raise ValueError(f"Birth year {year} looks off.")
        if month == 2 and day == 29 and not calendar.isleap(year):
            raise ValueError(f"{year} wasn't a leap year, so it had no 29 February.")
    return year, month, day


def celebration_date(year: int, month: int, day: int, leap_fallback: str = "02-28") -> date:
    """The day the birthday is celebrated in `year` (handles 29 February)."""
    if month == 2 and day == 29 and not calendar.isleap(year):
        return date(year, 3, 1) if leap_fallback == "03-01" else date(year, 2, 28)
    return date(year, month, day)


def next_birthday(
    month: int, day: int, today: date | None = None, leap_fallback: str = "02-28"
) -> tuple[date, bool]:
    """Return (date of today's or the next birthday, whether it is today)."""
    today = today or date.today()
    this_year = celebration_date(today.year, month, day, leap_fallback)
    if this_year == today:
        return this_year, True
    if this_year > today:
        return this_year, False
    return celebration_date(today.year + 1, month, day, leap_fallback), False


# ---------------------------------------------------------------------------
# Wishes
# ---------------------------------------------------------------------------


def pick_wish(
    wishes: dict[str, list[str]], last: tuple[str, str] | None, rng: random.Random | None = None
) -> tuple[str, str]:
    """Pick a random (category, wish), never repeating the previous one."""
    rng = rng or random.Random()
    pool = [(cat, w) for cat, items in wishes.items() for w in items]
    if not pool:
        return "Love", "Happy birthday! 💗"
    choices = [p for p in pool if p != last] or pool
    return rng.choice(choices)


# ---------------------------------------------------------------------------
# Decorations and effects (pure CSS, no images)
# ---------------------------------------------------------------------------

HEART_EMOJIS = ["💗", "💖", "💕", "💞", "💓", "✨"]
SPARKLE_EMOJIS = ["✨", "⭐", "🌟", "💫", "💖"]


def _palette(theme: dict) -> list[str]:
    return [theme["pink"], theme["deep_pink"], theme["lavender"], theme["peach"], theme["gold"], "#ffffff"]


def background_html(theme: dict) -> str:
    """Hearts and sparkles drifting up behind the whole page."""
    rng = random.Random(7)
    items = []
    for _ in range(16):
        style = (
            f"--x:{rng.uniform(2, 96):.1f}vw;--dx:{rng.uniform(-6, 6):.1f}vw;"
            f"--d:{rng.uniform(16, 28):.1f}s;--delay:-{rng.uniform(0, 26):.1f}s;"
            f"font-size:{rng.uniform(14, 28):.0f}px"
        )
        items.append(f'<span class="float-item" style="{style}">{rng.choice(HEART_EMOJIS + ["⭐"])}</span>')
    return f'<div class="bg-layer zero-gap">{"".join(items)}</div>'


def balloons_html(theme: dict) -> str:
    colors = [theme["pink"], theme["lavender"], theme["peach"], theme["deep_pink"], theme["gold"]]
    spots = [("left", 2, 10), ("left", 11, 70), ("left", 3, 150), ("right", 4, 20), ("right", 12, 95), ("right", 2, 170)]
    out = []
    for i, (side, offset, top) in enumerate(spots):
        c = colors[i % len(colors)]
        style = (
            f"{side}:{offset}%;top:{top}px;--c:{c};--c2:{shade(c, 0.8)};"
            f"--d:{3 + i * 0.45:.2f}s;--delay:-{i * 0.7:.1f}s"
        )
        out.append(f'<div class="balloon" style="{style}"></div>')
    return "".join(out)


def cake_html(name: str, blown: bool = False) -> str:
    candles = "".join(
        f'<div class="candle{" tall" if i == 2 else ""}">'
        f'<div class="flame"></div><div class="smoke"></div><div class="smoke s2"></div></div>'
        for i in range(5)
    )
    state = "blown" if blown else "lit"
    return f"""
    <div class="cake-scene {state}">
      <div class="cake-glow"></div>
      <div class="candles">{candles}</div>
      <div class="tier tier-3"></div>
      <div class="tier tier-2"></div>
      <div class="tier tier-1"><span class="cake-name">{esc(name)}</span></div>
      <div class="plate"></div>
    </div>
    """


def gift_html(opened: bool) -> str:
    pops = ""
    if opened:
        rng = random.Random(11)
        pops = "".join(
            f'<span class="gift-pop" style="--dx:{rng.uniform(-130, 130):.0f}px;'
            f'--dy:{rng.uniform(-200, -110):.0f}px;--delay:{0.35 + i * 0.05:.2f}s">'
            f"{rng.choice(SPARKLE_EMOJIS + HEART_EMOJIS)}</span>"
            for i in range(14)
        )
    state = "open" if opened else "closed"
    return f"""
    <div class="gift-scene {state}">
      <div class="gift-glow"></div>
      <div class="gift-rays"></div>
      <div class="gift-body">
        <div class="gift-box"></div>
        <div class="gift-lid-group">
          <div class="gift-lid"></div>
          <div class="bow"><span class="loop l"></span><span class="loop r"></span><span class="knot"></span></div>
        </div>
      </div>
      {pops}
    </div>
    """


def _confetti(rng: random.Random, colors: list[str], count: int) -> str:
    pieces = []
    for _ in range(count):
        w = rng.randint(6, 11)
        h = round(w * rng.choice([0.5, 1, 1.6]))
        radius = "50%" if rng.random() < 0.3 else "2px"
        style = (
            f"--x:{rng.uniform(0, 100):.1f}vw;--dx:{rng.uniform(-18, 18):.1f}vw;"
            f"--r:{rng.randint(360, 1080)}deg;--d:{rng.uniform(2.6, 4.4):.2f}s;"
            f"--delay:{rng.uniform(0, 0.9):.2f}s;--c:{rng.choice(colors)};"
            f"width:{w}px;height:{h}px;border-radius:{radius}"
        )
        pieces.append(f'<i class="confetti" style="{style}"></i>')
    return "".join(pieces)


def _rising(rng: random.Random, emojis: list[str], count: int) -> str:
    items = []
    for _ in range(count):
        style = (
            f"--x:{rng.uniform(0, 96):.1f}vw;--dx:{rng.uniform(-10, 10):.1f}vw;"
            f"--d:{rng.uniform(3, 5.5):.2f}s;--delay:{rng.uniform(0, 1.6):.2f}s;"
            f"font-size:{rng.uniform(18, 38):.0f}px"
        )
        items.append(f'<span class="rise" style="{style}">{rng.choice(emojis)}</span>')
    return "".join(items)


def _twinkles(rng: random.Random, count: int) -> str:
    items = []
    for _ in range(count):
        style = (
            f"left:{rng.uniform(3, 95):.1f}vw;top:{rng.uniform(5, 85):.1f}vh;"
            f"--delay:{rng.uniform(0, 1.8):.2f}s;font-size:{rng.uniform(16, 34):.0f}px"
        )
        items.append(f'<span class="twinkle" style="{style}">{rng.choice(SPARKLE_EMOJIS)}</span>')
    return "".join(items)


def _bursts(rng: random.Random, colors: list[str], count: int, loop: bool, area: tuple = (10, 90, 10, 55)) -> str:
    unit = "%" if loop else "vw"
    vunit = "%" if loop else "vh"
    bursts = []
    for b in range(count):
        color = rng.choice(colors)
        delay = b * (0.55 if loop else 0.45) + rng.uniform(0, 0.3)
        radius = rng.uniform(55, 95)
        sparks = []
        for s in range(14):
            angle = 2 * math.pi * s / 14
            sparks.append(
                f'<i class="spark" style="--dx:{math.cos(angle) * radius:.0f}px;'
                f'--dy:{math.sin(angle) * radius:.0f}px;--c:{color};--delay:{delay:.2f}s"></i>'
            )
        pos = (
            f"left:{rng.uniform(area[0], area[1]):.0f}{unit};"
            f"top:{rng.uniform(area[2], area[3]):.0f}{vunit}"
        )
        bursts.append(f'<div class="burst{" loop" if loop else ""}" style="{pos}">{"".join(sparks)}</div>')
    return "".join(bursts)


def effects_html(kind: str | None, fx_id: int, theme: dict) -> str:
    """A full-screen, click-through overlay for one celebration effect.

    The content depends only on (kind, fx_id), so unrelated reruns leave it
    untouched and the animation does not replay. Alternating the wrapper tag
    forces a fresh mount each time a new effect is triggered.
    """
    if not kind:
        return '<div class="zero-gap"></div>'
    rng = random.Random(fx_id)
    colors = _palette(theme)
    parts = {
        "confetti": lambda: _confetti(rng, colors, 110) + _rising(rng, HEART_EMOJIS, 10),
        "hearts": lambda: _rising(rng, HEART_EMOJIS, 34),
        "sparkles": lambda: _twinkles(rng, 22) + _rising(rng, HEART_EMOJIS, 10),
        "gift": lambda: _rising(rng, HEART_EMOJIS, 26) + _twinkles(rng, 18),
        "grand": lambda: _confetti(rng, colors, 120)
        + _rising(rng, HEART_EMOJIS, 22)
        + _bursts(rng, colors, 6, loop=False),
    }
    inner = parts.get(kind, parts["confetti"])()
    tag = "section" if fx_id % 2 else "div"
    return f'<{tag} class="fx-layer zero-gap">{inner}</{tag}>'


def night_sky_html(title: str, theme: dict) -> str:
    rng = random.Random(21)
    stars = "".join(
        f'<i class="star" style="left:{rng.uniform(0, 100):.1f}%;top:{rng.uniform(0, 100):.1f}%;'
        f'--delay:-{rng.uniform(0, 3):.1f}s;width:{rng.choice([2, 2, 3])}px;height:{rng.choice([2, 2, 3])}px"></i>'
        for _ in range(45)
    )
    colors = [theme["pink"], theme["gold"], theme["lavender"], theme["peach"], "#ffffff"]
    fireworks = _bursts(rng, colors, 5, loop=True, area=(10, 90, 12, 50))
    return f"""
    <div class="night-sky">
      {stars}{fireworks}
      <div class="finale-title">{gradient_text(title)}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Live countdown (runs in the browser, so no Streamlit reruns are needed)
# ---------------------------------------------------------------------------


def countdown_html(target: date, name: str, theme: dict) -> str:
    return f"""
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&family=Dancing+Script:wght@700&display=swap');
html,body{{margin:0;background:transparent;font-family:'Quicksand','Segoe UI',sans-serif;color:{theme['text']};}}
.wrap{{display:flex;flex-wrap:wrap;gap:clamp(6px,2vw,12px);justify-content:center;padding:8px 4px 4px;}}
.unit{{box-sizing:border-box;width:clamp(60px,20vw,104px);padding:16px 0 12px;border-radius:22px;text-align:center;
  background:linear-gradient(160deg,rgba(255,255,255,.95),{theme['cream']});
  border:1.5px solid {theme['gold']}88;box-shadow:0 10px 26px rgba(170,100,160,.18);}}
.num{{font-size:clamp(28px,7vw,42px);font-weight:700;color:{theme['deep_pink']};line-height:1;display:inline-block;}}
.num.tick{{animation:tick .45s ease;}}
.label{{margin-top:6px;font-size:clamp(9px,2.8vw,12px);letter-spacing:.14em;text-transform:uppercase;color:{theme['muted']};}}
.done{{display:none;text-align:center;font-family:'Dancing Script',cursive;font-size:30px;color:{theme['deep_pink']};padding:24px 8px;}}
@keyframes tick{{0%{{transform:scale(1.25)}}100%{{transform:scale(1)}}}}
</style></head><body>
<div class="wrap" id="wrap">
  <div class="unit"><div class="num" id="d">--</div><div class="label">Days</div></div>
  <div class="unit"><div class="num" id="h">--</div><div class="label">Hours</div></div>
  <div class="unit"><div class="num" id="m">--</div><div class="label">Minutes</div></div>
  <div class="unit"><div class="num" id="s">--</div><div class="label">Seconds</div></div>
</div>
<div class="done" id="done">It's your birthday, {esc(name)}! 🎉 Refresh to celebrate 💗</div>
<script>
const target = new Date({target.year}, {target.month - 1}, {target.day}, 0, 0, 0);
const pad = n => String(n).padStart(2, "0");
function set(id, value) {{
  const el = document.getElementById(id);
  if (el.textContent !== value) {{
    el.textContent = value;
    el.classList.remove("tick"); void el.offsetWidth; el.classList.add("tick");
  }}
}}
function update() {{
  let diff = Math.floor((target - new Date()) / 1000);
  if (diff <= 0) {{
    document.getElementById("wrap").style.display = "none";
    document.getElementById("done").style.display = "block";
    return false;
  }}
  set("d", String(Math.floor(diff / 86400)));
  set("h", pad(Math.floor(diff % 86400 / 3600)));
  set("m", pad(Math.floor(diff % 3600 / 60)));
  set("s", pad(diff % 60));
  return true;
}}
if (update()) {{ const t = setInterval(() => {{ if (!update()) clearInterval(t); }}, 1000); }}
</script></body></html>
"""


# Browsers only allow sound after the visitor has interacted with the page. This
# tries to start the docked song right away and, if that is blocked, starts it on
# the first click, tap or key press anywhere. Once it has started, pausing is
# respected and nothing restarts it.
AUTOPLAY_HELPER = """
<!doctype html><html><body style="margin:0"><script>
const doc = window.parent.document;
const events = ["pointerdown", "touchstart", "keydown"];
let started = false;
const findAudio = () => doc.querySelector(".st-key-music_dock audio");
function markStarted() {
  started = true;
  events.forEach(e => doc.removeEventListener(e, tryPlay, true));
}
function tryPlay() {
  const audio = findAudio();
  if (started || !audio) return;
  if (!audio.paused) { markStarted(); return; }
  audio.play().then(markStarted).catch(() => {});
}
events.forEach(e => doc.addEventListener(e, tryPlay, true));
let tries = 0;
const timer = setInterval(() => {
  tryPlay();
  if (started || ++tries > 40) clearInterval(timer);
}, 250);
</script></body></html>
"""


# ---------------------------------------------------------------------------
# Global stylesheet
# ---------------------------------------------------------------------------


def css(theme: dict) -> str:
    variables = (
        ":root{"
        f"--pink:{theme['pink']};--deep-pink:{theme['deep_pink']};--lavender:{theme['lavender']};"
        f"--cream:{theme['cream']};--peach:{theme['peach']};--gold:{theme['gold']};"
        f"--text:{theme['text']};--muted:{theme['muted']};"
        f"--deep-lavender:{shade(theme['lavender'], 0.82)};--deep-peach:{shade(theme['peach'], 0.9)};"
        f"--pink-2:{shade(theme['pink'], 0.88)};"
        "}"
    )
    return f"<style>{_FONTS}{variables}{_CSS}</style>"


_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@500;700"
    "&family=Great+Vibes&family=Quicksand:wght@400;500;600;700"
    "&family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&display=swap');"
)

_CSS = """
/* ---------- page ---------- */
.stApp{
  background:
    radial-gradient(circle at 12% 8%, rgba(255,211,184,.55), transparent 40%),
    radial-gradient(circle at 88% 18%, rgba(201,182,242,.5), transparent 45%),
    radial-gradient(circle at 50% 105%, rgba(247,168,196,.45), transparent 55%),
    linear-gradient(180deg,#fff8f3 0%,#fdf0f6 100%);
  background-attachment:fixed;color:var(--text);
}
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none !important;}
.block-container,[data-testid="stMainBlockContainer"]{max-width:820px;padding-top:2.2rem;padding-bottom:9rem;position:relative;z-index:1;}
[data-testid="stElementContainer"]:has(.zero-gap){margin-bottom:-1rem;}
[data-testid="stElementContainer"]:has(.stButton){align-self:center;width:auto !important;}
.emoji{-webkit-text-fill-color:initial;background:none;font-family:"Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif;}

/* ---------- typography ---------- */
.kicker{text-align:center;font-family:'Quicksand',sans-serif;font-size:.78rem;letter-spacing:.35em;text-transform:uppercase;color:var(--muted);font-weight:600;}
.script-title{
  font-family:'Great Vibes',cursive;font-weight:400;text-align:center;line-height:1.1;margin:.2rem 0 .6rem;
  font-size:clamp(3rem,11vw,5.4rem);
  background:linear-gradient(90deg,var(--deep-pink),var(--deep-lavender),var(--gold),var(--deep-pink));
  background-size:300% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  animation:shimmer 7s linear infinite;padding:0 .2em;
}
.subtitle{text-align:center;font-family:'Quicksand',sans-serif;font-size:clamp(1.02rem,2.8vw,1.2rem);color:var(--text);max-width:600px;margin:0 auto;line-height:1.7;}
.chapter{text-align:center;margin-top:3.2rem;}
.chapter .num{font-family:'Quicksand',sans-serif;font-size:.74rem;letter-spacing:.35em;text-transform:uppercase;color:var(--muted);font-weight:700;}
.chapter-title{font-family:'Great Vibes',cursive;font-weight:400;font-size:clamp(2.5rem,8vw,3.5rem);line-height:1.15;margin:.1rem 0 0;padding:0;
  background:linear-gradient(90deg,var(--deep-pink),var(--deep-lavender));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.chapter .ornament{color:var(--gold);letter-spacing:.6em;font-size:.9rem;margin-top:.2rem;}
.chapter p{font-family:'Quicksand',sans-serif;color:var(--muted);margin:.4rem auto 0;max-width:520px;}

/* ---------- cards ---------- */
.card{
  position:relative;max-width:620px;margin:1rem auto;padding:clamp(20px,4vw,32px);border-radius:28px;text-align:center;
  background:linear-gradient(150deg,rgba(255,255,255,.88),rgba(255,246,250,.82));
  border:1.5px solid rgba(255,255,255,.95);box-shadow:0 18px 50px rgba(170,100,160,.18),inset 0 0 0 1px rgba(230,194,122,.25);
  backdrop-filter:blur(10px);font-family:'Quicksand',sans-serif;color:var(--text);font-size:1.08rem;line-height:1.75;
}
.card.reveal{animation:reveal .8s cubic-bezier(.2,1.2,.4,1) both;}
.card .sign{font-family:'Dancing Script',cursive;font-size:1.5rem;color:var(--deep-pink);margin-top:.6rem;}
.card .card-title{font-family:'Dancing Script',cursive;font-size:2rem;color:var(--deep-pink);margin:0 0 .4rem;padding:0;}
.card .big{font-family:'Dancing Script',cursive;font-size:clamp(1.5rem,4.5vw,1.9rem);line-height:1.45;color:var(--text);}

/* ---------- buttons ---------- */
.stButton{display:flex;justify-content:center;}
button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,var(--deep-pink),#c48be0) !important;border:none !important;border-radius:999px !important;
  padding:.8rem 2rem !important;color:#fff !important;
  box-shadow:0 10px 26px rgba(232,103,154,.38),0 0 0 4px rgba(255,255,255,.7) !important;
  transition:transform .25s ease,box-shadow .25s ease !important;animation:glow 2.8s ease-in-out infinite;
}
button[data-testid="stBaseButton-primary"] p{font-family:'Quicksand',sans-serif !important;font-weight:700 !important;font-size:1.06rem !important;color:#fff !important;}
button[data-testid="stBaseButton-primary"]:hover{transform:translateY(-3px) scale(1.04);box-shadow:0 16px 34px rgba(232,103,154,.5),0 0 0 5px rgba(255,255,255,.85) !important;}
button[data-testid="stBaseButton-primary"]:active{transform:scale(.97);}
button[data-testid="stBaseButton-tertiary"] p{font-family:'Quicksand',sans-serif !important;color:var(--muted) !important;font-weight:600 !important;}
button[data-testid="stBaseButton-tertiary"]:hover p{color:var(--deep-pink) !important;}

/* ---------- background + effects ---------- */
.bg-layer,.fx-layer{position:fixed;inset:0;pointer-events:none;overflow:hidden;}
.bg-layer{z-index:0;}
.fx-layer{z-index:999999;}
.float-item{position:absolute;bottom:-8vh;left:var(--x);opacity:0;animation:float-up var(--d) linear var(--delay) infinite;}
.confetti{position:absolute;top:-4vh;left:var(--x);background:var(--c);opacity:0;animation:confetti-fall var(--d) cubic-bezier(.25,.6,.5,1) var(--delay) forwards;}
.rise{position:absolute;bottom:-8vh;left:var(--x);opacity:0;animation:rise var(--d) ease-out var(--delay) forwards;}
.twinkle{position:absolute;opacity:0;animation:twinkle-pop 1.6s ease-in-out var(--delay) 2 forwards;}
.burst{position:absolute;width:0;height:0;}
.spark{position:absolute;left:-3px;top:-3px;width:6px;height:6px;border-radius:50%;background:var(--c);box-shadow:0 0 10px 2px var(--c);opacity:0;animation:spark 1.5s ease-out var(--delay) forwards;}
.burst.loop .spark{animation:spark-loop 3s ease-out var(--delay) infinite;}

/* ---------- hero + balloons ---------- */
.hero{position:relative;padding:.5rem 0 0;}
.hero-content{position:relative;z-index:1;}
.balloons{position:absolute;inset:0;pointer-events:none;z-index:0;}
.balloon{position:absolute;width:56px;height:70px;border-radius:50% 50% 47% 47% / 55% 55% 45% 45%;
  background:radial-gradient(circle at 32% 28%,rgba(255,255,255,.85) 0 7%,var(--c) 38%,var(--c2) 100%);
  box-shadow:inset -6px -8px 14px rgba(0,0,0,.06);animation:bob var(--d) ease-in-out var(--delay) infinite alternate;opacity:.92;}
.balloon::before{content:"";position:absolute;bottom:-6px;left:50%;margin-left:-5px;border:5px solid transparent;border-bottom:7px solid var(--c2);transform:rotate(180deg);}
.balloon::after{content:"";position:absolute;top:calc(100% + 6px);left:50%;width:1px;height:60px;background:rgba(141,107,136,.45);}

/* ---------- cake ---------- */
.cake-scene{position:relative;width:280px;height:300px;margin:.8rem auto 0;}
.cake-glow{position:absolute;left:50%;top:10px;width:260px;height:150px;margin-left:-130px;border-radius:50%;
  background:radial-gradient(ellipse,rgba(255,210,120,.5),transparent 65%);animation:pulse 2.6s ease-in-out infinite;transition:opacity 1s;}
.cake-scene.blown .cake-glow{opacity:0;}
.plate{position:absolute;bottom:6px;left:50%;width:280px;height:28px;margin-left:-140px;border-radius:50%;background:linear-gradient(#fff,#efe1ec);box-shadow:0 10px 20px rgba(150,90,140,.25);}
.tier{position:absolute;left:50%;border-radius:16px 16px 10px 10px;overflow:hidden;box-shadow:inset 0 -6px 0 rgba(230,194,122,.55),0 6px 14px rgba(150,90,140,.15);}
.tier::before{content:"";position:absolute;top:0;left:0;right:0;height:26px;
  background:radial-gradient(circle at 50% 0,var(--cream) 0 10px,transparent 11px) 0 8px/20px 20px repeat-x,
             linear-gradient(var(--cream),var(--cream)) 0 0/100% 10px no-repeat;}
.tier::after{content:"";position:absolute;inset:30px 10px 10px;
  background:radial-gradient(circle,var(--gold) 2.4px,transparent 3px) 0 0/34px 22px,
             radial-gradient(circle,#fff 2px,transparent 2.6px) 17px 11px/34px 22px;opacity:.9;}
.tier-1{bottom:22px;width:240px;height:78px;margin-left:-120px;background:linear-gradient(180deg,var(--pink),var(--pink-2));}
.tier-2{bottom:98px;width:186px;height:64px;margin-left:-93px;background:linear-gradient(180deg,var(--lavender),var(--deep-lavender));}
.tier-3{bottom:160px;width:132px;height:54px;margin-left:-66px;background:linear-gradient(180deg,var(--peach),var(--deep-peach));}
.cake-name{position:absolute;left:0;right:0;top:26px;z-index:2;text-align:center;font-family:'Great Vibes',cursive;font-size:2rem;color:#fff;text-shadow:0 2px 6px rgba(200,80,130,.55);}
.candles{position:absolute;bottom:212px;left:50%;transform:translateX(-50%);display:flex;gap:14px;align-items:flex-end;z-index:3;}
.candle{position:relative;width:11px;height:40px;border-radius:4px 4px 2px 2px;background:repeating-linear-gradient(45deg,#fff 0 6px,var(--deep-pink) 6px 10px);box-shadow:0 2px 4px rgba(0,0,0,.08);}
.candle.tall{height:50px;}
.candle::before{content:"";position:absolute;top:-7px;left:50%;width:2px;height:7px;margin-left:-1px;background:#6d4a63;border-radius:1px;}
.flame{position:absolute;top:-33px;left:50%;width:14px;height:24px;margin-left:-7px;border-radius:50% 50% 35% 35% / 60% 60% 40% 40%;
  background:radial-gradient(circle at 50% 72%,#fffbe0 0 18%,#ffd25e 45%,#ff8a3d 85%);
  box-shadow:0 0 12px 4px rgba(255,190,80,.7),0 0 34px 12px rgba(255,170,60,.3);transform-origin:50% 90%;animation:flicker .8s ease-in-out infinite alternate;}
.candle:nth-child(2n) .flame{animation-duration:.65s;animation-delay:-.3s;}
.cake-scene.blown .flame{animation:blow-out .55s ease-in forwards;}
.smoke{position:absolute;top:-22px;left:50%;width:8px;height:8px;margin-left:-4px;border-radius:50%;background:rgba(205,195,215,.45);filter:blur(3px);opacity:0;}
.cake-scene.blown .smoke{animation:smoke 2.2s ease-out .35s forwards;}
.cake-scene.blown .smoke.s2{animation-delay:.8s;}

/* ---------- letter ---------- */
.envelope{position:relative;width:min(340px,86vw);aspect-ratio:16/10;margin:1.2rem auto .4rem;border-radius:14px;
  background:linear-gradient(160deg,#fff6fa,#f9dfeb);box-shadow:0 22px 44px rgba(170,100,160,.25);overflow:hidden;animation:float-soft 4s ease-in-out infinite;}
.envelope::after{content:"";position:absolute;inset:0;background:linear-gradient(200deg,#fbe7f0,#f3cfe0);clip-path:polygon(0 100%,50% 48%,100% 100%);}
.envelope::before{content:"";position:absolute;top:0;left:0;right:0;height:62%;z-index:1;background:linear-gradient(180deg,#f8d3e3,#f2bdd5);clip-path:polygon(0 0,100% 0,50% 100%);}
.seal{position:absolute;top:50%;left:50%;width:56px;height:56px;margin:-22px 0 0 -28px;z-index:2;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#f9a8c7,var(--deep-pink));box-shadow:0 6px 14px rgba(200,70,120,.4),inset 0 0 0 4px rgba(255,255,255,.25);
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.5rem;animation:heartbeat 1.6s ease-in-out infinite;}
.env-to{position:absolute;bottom:10px;left:0;right:0;z-index:2;text-align:center;font-family:'Dancing Script',cursive;font-size:1.4rem;color:var(--deep-pink);}
.letter{position:relative;max-width:640px;margin:1.2rem auto .6rem;padding:clamp(26px,6vw,54px);border-radius:8px;
  background:radial-gradient(circle at 100% 0,rgba(247,168,196,.18),transparent 30%),radial-gradient(circle at 0 100%,rgba(201,182,242,.2),transparent 35%),var(--cream);
  border:1px solid rgba(230,194,122,.55);box-shadow:0 26px 60px rgba(120,70,120,.2),inset 0 0 0 10px #fffdf8,inset 0 0 0 11px rgba(230,194,122,.45);
  transform-origin:top center;animation:unfold 1s cubic-bezier(.2,.9,.25,1) both;}
.letter .flourish{text-align:center;color:var(--gold);letter-spacing:.5em;margin-bottom:.6rem;}
.letter .greeting{font-family:'Dancing Script',cursive;font-size:clamp(1.8rem,5vw,2.3rem);color:var(--deep-pink);margin-bottom:.8rem;}
.letter p{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(1.12rem,2.8vw,1.28rem);line-height:1.75;color:var(--text);margin:0 0 1rem;}
.letter .signoff{text-align:right;font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-size:1.15rem;color:var(--muted);margin-top:1.4rem;}
.letter .name{text-align:right;font-family:'Great Vibes',cursive;font-size:clamp(2.2rem,6vw,2.8rem);color:var(--deep-pink);line-height:1.2;}

/* ---------- gift ---------- */
.gift-scene{position:relative;width:260px;height:270px;margin:4.5rem auto 0;}
.gift-glow{position:absolute;left:50%;bottom:0;width:300px;height:260px;margin-left:-150px;border-radius:50%;background:radial-gradient(circle,rgba(255,214,140,.55),transparent 62%);filter:blur(6px);animation:pulse 2.4s ease-in-out infinite;}
.gift-rays{position:absolute;left:50%;bottom:120px;width:280px;height:280px;margin-left:-140px;border-radius:50%;opacity:0;
  background:repeating-conic-gradient(rgba(255,226,150,.55) 0 10deg,transparent 10deg 24deg);
  -webkit-mask:radial-gradient(circle,#000 20%,transparent 68%);mask:radial-gradient(circle,#000 20%,transparent 68%);}
.gift-scene.open .gift-rays{animation:rays-in .8s ease-out .3s forwards,spin 14s linear infinite;}
.gift-body{position:absolute;inset:0;transform-origin:50% 100%;}
.gift-scene.closed .gift-body{animation:wiggle 3.2s ease-in-out infinite;}
.gift-box{position:absolute;bottom:0;left:50%;width:190px;height:150px;margin-left:-95px;border-radius:10px;
  background:linear-gradient(135deg,var(--deep-pink),var(--pink));box-shadow:0 20px 40px rgba(200,80,130,.3),inset 0 -10px 0 rgba(0,0,0,.05);}
.gift-box::before{content:"";position:absolute;top:0;bottom:0;left:50%;width:30px;margin-left:-15px;background:linear-gradient(90deg,#d9ad5c,#f6dc9c,#d9ad5c);}
.gift-box::after{content:"";position:absolute;top:0;left:0;right:0;height:18px;background:linear-gradient(rgba(0,0,0,.08),transparent);}
.gift-lid-group{position:absolute;left:50%;bottom:146px;width:214px;height:44px;margin-left:-107px;transform-origin:15% 100%;}
.gift-scene.open .gift-lid-group{animation:lid-off 1s cubic-bezier(.3,1.3,.5,1) forwards;}
.gift-lid{position:absolute;inset:0;border-radius:9px;background:linear-gradient(135deg,#f07aa7,var(--pink));box-shadow:0 8px 16px rgba(200,80,130,.25);}
.gift-lid::before{content:"";position:absolute;top:0;bottom:0;left:50%;width:30px;margin-left:-15px;background:linear-gradient(90deg,#d9ad5c,#f6dc9c,#d9ad5c);}
.bow{position:absolute;left:50%;bottom:40px;width:0;height:0;}
.bow .loop{position:absolute;bottom:-6px;width:52px;height:38px;border:9px solid #e7c071;border-radius:50%;box-sizing:border-box;}
.bow .loop.l{right:2px;transform:rotate(-28deg);}
.bow .loop.r{left:2px;transform:rotate(28deg);}
.bow .knot{position:absolute;left:-12px;bottom:-12px;width:24px;height:24px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fbe6b0,#d9ad5c);}
.gift-pop{position:absolute;left:50%;bottom:150px;font-size:26px;opacity:0;animation:gift-pop 1.6s ease-out var(--delay) forwards;}

/* ---------- wishes ---------- */
.wish-card{position:relative;max-width:560px;margin:1.2rem auto .4rem;padding:36px 30px 32px;border-radius:30px;text-align:center;
  background:linear-gradient(140deg,rgba(255,255,255,.95),rgba(255,238,246,.92) 60%,rgba(240,232,255,.92));
  border:1.5px solid rgba(230,194,122,.6);box-shadow:0 20px 50px rgba(170,100,160,.2);animation:wish-pop .75s cubic-bezier(.2,1.4,.4,1) both;}
.wish-card.empty{animation:none;opacity:.85;}
.wish-tag{display:inline-block;padding:4px 14px;border-radius:999px;font-family:'Quicksand',sans-serif;font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--deep-pink),var(--deep-lavender));}
.wish-text{font-family:'Dancing Script',cursive;font-size:clamp(1.5rem,4.6vw,2rem);line-height:1.45;color:var(--text);margin-top:.9rem;}
.wish-count{font-family:'Quicksand',sans-serif;font-size:.8rem;color:var(--muted);margin-top:.8rem;}
.corner{position:absolute;color:var(--gold);font-size:1.1rem;animation:twinkle 2s ease-in-out infinite;}
.corner.tl{top:14px;left:18px;}.corner.tr{top:14px;right:18px;animation-delay:.5s;}
.corner.bl{bottom:14px;left:18px;animation-delay:1s;}.corner.br{bottom:14px;right:18px;animation-delay:1.5s;}

/* ---------- finale ---------- */
.night-sky{position:relative;overflow:hidden;border-radius:32px;min-height:320px;margin:1.2rem auto 0;display:flex;align-items:center;justify-content:center;padding:40px 24px;
  background:radial-gradient(ellipse at 50% 120%,#7a4a86 0%,#3d2456 45%,#21143a 100%);box-shadow:0 26px 60px rgba(60,30,80,.35);}
.star{position:absolute;border-radius:50%;background:#fff;animation:twinkle 3s ease-in-out var(--delay) infinite;}
.finale-title{position:relative;z-index:2;text-align:center;font-family:'Great Vibes',cursive;font-weight:400;font-size:clamp(2.1rem,6.4vw,3.3rem);line-height:1.25;margin:0;padding:0;
  background:linear-gradient(90deg,#fff,#ffd6e7,#f6dc9c,#fff);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  animation:shimmer 6s linear infinite;filter:drop-shadow(0 0 14px rgba(255,190,220,.45));}
.music-label{text-align:center;font-family:'Quicksand',sans-serif;color:var(--muted);font-weight:600;margin-top:1.4rem;}
.countdown-date{margin-top:-.4rem;}
audio[data-testid="stAudio"]{display:block;width:100%;max-width:460px;margin:0 auto;}
.st-key-music_dock{position:fixed !important;left:50%;bottom:14px;transform:translateX(-50%);z-index:1000000;
  width:min(440px,calc(100vw - 24px)) !important;gap:2px !important;padding:8px 12px 10px;border-radius:24px;
  background:rgba(255,255,255,.85);backdrop-filter:blur(12px);border:1.5px solid rgba(230,194,122,.55);box-shadow:0 14px 34px rgba(170,100,160,.3);}
.st-key-music_dock [data-testid="stElementContainer"]:has(iframe){display:none;}
.st-key-music_dock audio{height:40px;}
.st-key-music_dock [data-testid="stMarkdown"],.st-key-music_dock [data-testid="stMarkdownContainer"]{margin-bottom:0 !important;}
.dock-label{text-align:center;font-family:'Quicksand',sans-serif;font-weight:700;font-size:.85rem;color:var(--deep-pink);}
.footer{text-align:center;font-family:'Dancing Script',cursive;font-size:1.3rem;color:var(--muted);margin-top:2.6rem;}

/* ---------- keyframes ---------- */
@keyframes shimmer{to{background-position:300% 0;}}
@keyframes glow{0%,100%{filter:brightness(1);}50%{filter:brightness(1.08) drop-shadow(0 0 10px rgba(232,103,154,.45));}}
@keyframes pulse{0%,100%{opacity:.75;transform:scale(1);}50%{opacity:1;transform:scale(1.06);}}
@keyframes float-up{0%{opacity:0;transform:translate(0,0) rotate(0);}10%{opacity:.55;}85%{opacity:.45;}100%{opacity:0;transform:translate(var(--dx),-115vh) rotate(25deg);}}
@keyframes float-soft{0%,100%{transform:translateY(0);}50%{transform:translateY(-8px);}}
@keyframes bob{0%{transform:translateY(0) rotate(-5deg);}100%{transform:translateY(-20px) rotate(5deg);}}
@keyframes confetti-fall{0%{opacity:1;transform:translate(0,0) rotate(0);}85%{opacity:1;}100%{opacity:0;transform:translate(var(--dx),108vh) rotate(var(--r));}}
@keyframes rise{0%{opacity:0;transform:translate(0,0) scale(.6);}12%{opacity:1;}80%{opacity:.9;}100%{opacity:0;transform:translate(var(--dx),-112vh) scale(1.15);}}
@keyframes twinkle-pop{0%{opacity:0;transform:scale(0) rotate(0);}50%{opacity:1;transform:scale(1.2) rotate(90deg);}100%{opacity:0;transform:scale(0) rotate(180deg);}}
@keyframes twinkle{0%,100%{opacity:.35;transform:scale(.85);}50%{opacity:1;transform:scale(1.15);}}
@keyframes spark{0%{opacity:1;transform:translate(0,0) scale(1);}100%{opacity:0;transform:translate(var(--dx),calc(var(--dy) + 30px)) scale(.3);}}
@keyframes spark-loop{0%{opacity:0;transform:translate(0,0) scale(1);}6%{opacity:1;}55%{opacity:.85;transform:translate(var(--dx),calc(var(--dy) + 20px)) scale(.5);}65%,100%{opacity:0;transform:translate(var(--dx),calc(var(--dy) + 28px)) scale(.3);}}
@keyframes flicker{0%{transform:scale(1,1) rotate(-2deg);}50%{transform:scale(.9,1.1) rotate(2deg);}100%{transform:scale(1.06,.94) rotate(-1deg);}}
@keyframes blow-out{0%{opacity:1;transform:scale(1);}40%{opacity:.8;transform:skewX(-28deg) scale(.8,.55) translateX(-5px);}100%{opacity:0;transform:scale(0);}}
@keyframes smoke{0%{opacity:.75;transform:translate(0,0) scale(.6);}100%{opacity:0;transform:translate(-10px,-70px) scale(3.2);}}
@keyframes heartbeat{0%,100%{transform:scale(1);}15%{transform:scale(1.12);}30%{transform:scale(1);}45%{transform:scale(1.08);}}
@keyframes unfold{0%{opacity:0;transform:perspective(900px) rotateX(-70deg) translateY(-20px);}100%{opacity:1;transform:none;}}
@keyframes reveal{0%{opacity:0;transform:translateY(24px) scale(.94);}100%{opacity:1;transform:none;}}
@keyframes wish-pop{0%{opacity:0;transform:scale(.7) rotate(-3deg);}100%{opacity:1;transform:none;}}
@keyframes wiggle{0%,78%,100%{transform:rotate(0);}82%{transform:rotate(-5deg);}86%{transform:rotate(5deg);}90%{transform:rotate(-3deg);}94%{transform:rotate(2deg);}}
@keyframes lid-off{0%{transform:none;}40%{transform:translateY(-70px) rotate(-8deg);}100%{transform:translate(-95px,-30px) rotate(-38deg);}}
@keyframes rays-in{to{opacity:1;}}
@keyframes spin{to{transform:rotate(360deg);}}
@keyframes gift-pop{0%{opacity:0;transform:translate(-50%,0) scale(.4);}20%{opacity:1;}100%{opacity:0;transform:translate(calc(-50% + var(--dx)),var(--dy)) scale(1.2);}}

/* ---------- small screens ---------- */
@media (max-width:640px){
  .block-container,[data-testid="stMainBlockContainer"]{padding-left:1rem;padding-right:1rem;padding-top:1.2rem;}
  .balloon{width:40px;height:50px;opacity:.55;}
  .balloon:nth-child(3n){display:none;}
  .chapter{margin-top:2.4rem;}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;}
}
"""
