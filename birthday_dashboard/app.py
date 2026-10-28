"""A magical birthday surprise for Tommy. Run with:  streamlit run app.py"""

from datetime import date
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import config
from utils import helpers as h

APP_DIR = Path(__file__).parent
NAME = config.SISTER_NAME
THEME = config.THEME

st.set_page_config(
    page_title=f"Happy Birthday, {NAME}!",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# State and button callbacks (callbacks run before the rerun, so one click
# means exactly one rerun)
# ---------------------------------------------------------------------------

DEFAULTS = {
    "opened": False,
    "wished": False,
    "letter_open": False,
    "gift_stage": 0,  # 0 = wrapped, 1 = opened, 2 = second surprise shown
    "wish": None,
    "wish_count": 0,
    "fx": None,
    "fx_id": 0,
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)
state = st.session_state


def celebrate(kind: str) -> None:
    state.fx = kind
    state.fx_id += 1


def open_surprise() -> None:
    state.opened = True
    celebrate("confetti")


def make_wish() -> None:
    state.wished = True
    celebrate("hearts")


def relight_candles() -> None:
    state.wished = False


def toggle_letter() -> None:
    state.letter_open = not state.letter_open
    if state.letter_open:
        celebrate("sparkles")


def open_gift() -> None:
    state.gift_stage = 1
    celebrate("gift")


def second_surprise() -> None:
    state.gift_stage = 2
    celebrate("sparkles")


def rewrap_gift() -> None:
    state.gift_stage = 0


def new_wish() -> None:
    state.wish = h.pick_wish(config.BIRTHDAY_WISHES, state.wish)
    state.wish_count += 1


def start_over() -> None:
    fx_id = state.fx_id
    for key, value in DEFAULTS.items():
        state[key] = value
    state.fx_id = fx_id  # keep counting so the next effect still mounts fresh


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def chapter(number: int, title: str, note: str = "") -> None:
    note_html = f"<p>{h.esc(note)}</p>" if note else ""
    h.render(
        f"""
        <div class="chapter">
          <div class="num">Chapter {number}</div>
          <div class="chapter-title">{h.esc(title)}</div>
          <div class="ornament">✦ ✦ ✦</div>
          {note_html}
        </div>
        """
    )


def welcome_screen() -> None:
    h.render(
        f"""
        <div class="hero">
          <div class="balloons">{h.balloons_html(THEME)}</div>
          <div class="hero-content">
            <div class="kicker">✦ a little surprise, made with love ✦</div>
            <div class="script-title">{h.gradient_text(config.WELCOME_TITLE)}</div>
            <div class="subtitle">{h.esc(config.WELCOME_SUBTITLE)}</div>
            {h.cake_html(NAME)}
          </div>
        </div>
        <div class="card">
          {h.esc(config.WELCOME_CARD)}
          <div class="sign">— {h.esc(config.YOUR_NAME)} 💗</div>
        </div>
        """
    )
    st.button("Open Your Surprise 🎁", type="primary", on_click=open_surprise, key="open_surprise")


def journey_intro() -> None:
    h.render(
        f"""
        <div class="hero">
          <div class="balloons">{h.balloons_html(THEME)}</div>
          <div class="hero-content">
            <div class="kicker">✦ the celebration has begun ✦</div>
            <div class="script-title">{h.gradient_text(f"For you, {NAME} 💗")}</div>
            <div class="subtitle">Six little chapters, all about you. Scroll slowly and click everything.</div>
          </div>
        </div>
        """
    )


def cake_section() -> None:
    chapter(1, f"Make a Wish, {NAME}!", "Close your eyes, think of something wonderful, then blow out the candles.")
    h.render(h.cake_html(NAME, blown=state.wished))
    if state.wished:
        h.render(f'<div class="card reveal"><div class="big">{h.esc(config.WISH_MESSAGE)}</div></div>')
        st.button("Light the candles again 🕯️", type="tertiary", on_click=relight_candles, key="relight")
    else:
        st.button(f"Make a Wish, {NAME}! 🌬️", type="primary", on_click=make_wish, key="make_wish")


def letter_section() -> None:
    chapter(2, "A Letter For You", "Some things deserve to be written down.")
    if state.letter_open:
        h.render(
            f"""
            <div class="letter">
              <div class="flourish">❦ ✿ ❦</div>
              <div class="greeting">{h.esc(config.LETTER_GREETING)}</div>
              {h.paragraphs(config.LETTER_BODY)}
              <div class="signoff">{h.esc(config.LETTER_SIGNOFF)}</div>
              <div class="name">{h.esc(config.YOUR_NAME)}</div>
            </div>
            """
        )
        st.button("Fold the letter away 💌", type="tertiary", on_click=toggle_letter, key="close_letter")
    else:
        h.render(
            f"""
            <div class="envelope">
              <div class="seal">♥</div>
              <div class="env-to">For {h.esc(NAME)}</div>
            </div>
            """
        )
        st.button("Open Your Letter 💌", type="primary", on_click=toggle_letter, key="open_letter")


def gift_section() -> None:
    chapter(3, "A Secret Gift", "Something wrapped up just for you.")
    h.render(h.gift_html(opened=state.gift_stage > 0))
    if state.gift_stage == 0:
        st.button("Open the Gift 🎁", type="primary", on_click=open_gift, key="open_gift")
        return

    h.render(
        f"""
        <div class="card reveal">
          <div class="card-title">{h.esc(config.SECRET_GIFT_TITLE)}</div>
          <div class="big">{h.esc(config.SECRET_GIFT_MESSAGE)}</div>
        </div>
        """
    )
    if state.gift_stage == 1:
        st.button("One More Surprise 💝", type="primary", on_click=second_surprise, key="second_surprise")
    else:
        h.render(
            f"""
            <div class="card reveal">
              <div class="card-title">{h.esc(config.SECOND_SURPRISE_TITLE)}</div>
              <div class="big">{h.esc(config.SECOND_SURPRISE_MESSAGE)}</div>
            </div>
            """
        )
    st.button("Wrap it up again 🎀", type="tertiary", on_click=rewrap_gift, key="rewrap")


def wishes_section() -> None:
    chapter(4, "Little Wishes", "Tap as many times as you like — there's plenty of love to go around.")
    corners = '<span class="corner tl">✦</span><span class="corner tr">✦</span><span class="corner bl">✦</span><span class="corner br">✦</span>'
    if state.wish:
        category, text = state.wish
        # Alternate the tag so every new wish remounts and replays its animation.
        tag = "section" if state.wish_count % 2 else "div"
        h.render(
            f"""
            <{tag} class="wish-card">{corners}
              <span class="wish-tag">{h.esc(category)}</span>
              <div class="wish-text">{h.esc(text)}</div>
              <div class="wish-count">wish #{state.wish_count} 💫</div>
            </{tag}>
            """
        )
    else:
        h.render(
            f"""
            <div class="wish-card empty">{corners}
              <span class="wish-tag">Waiting for you</span>
              <div class="wish-text">A little wish is ready and waiting… ✨</div>
            </div>
            """
        )
    st.button(f"A Little Wish for {NAME} 💖", type="primary", on_click=new_wish, key="new_wish")


def countdown_section() -> None:
    chapter(5, "Counting the Moments", f"Until the next time the whole world celebrates {NAME}.")
    try:
        year, month, day = h.parse_birthday(config.BIRTHDAY)
        fallback = config.LEAP_DAY_CELEBRATION if config.LEAP_DAY_CELEBRATION in ("02-28", "03-01") else "02-28"
    except ValueError as err:
        h.render(
            f"""
            <div class="card">
              <div class="card-title">Almost ready ⏳</div>
              Add {h.esc(NAME)}'s birthday to <b>config.py</b> (for example <b>BIRTHDAY = "08-14"</b>)
              to start the countdown.<br><small>{h.esc(err)}</small>
            </div>
            """
        )
        return

    today = date.today()
    target, is_today = h.next_birthday(month, day, today, fallback)
    age = target.year - year if year else None

    if is_today:
        age_text = f" — {age} years of wonderful" if age else ""
        h.render(
            f"""
            <div class="card reveal">
              <div class="card-title">It's today! 🎉</div>
              <div class="big">Today is the day, {h.esc(NAME)}! The countdown is over —
              now it's time to celebrate you{age_text}. 💗</div>
            </div>
            """
        )
        return

    countdown = h.countdown_html(target, NAME, THEME)
    if hasattr(st, "iframe"):  # Streamlit 1.5x+
        st.iframe(countdown, height=118)
    else:
        components.html(countdown, height=150)
    age_text = f" · turning {age}" if age else ""
    h.render(f'<div class="music-label countdown-date">🎈 {target.strftime("%A, %d %B %Y")}{age_text} 🎈</div>')


def finale_section() -> None:
    chapter(6, "The Grand Finale")
    h.render(h.night_sky_html(config.FINAL_TITLE, THEME))
    h.render(f'<div class="card"><div class="big">{h.esc(config.FINAL_MESSAGE)}</div></div>')
    st.button("Celebrate Again 🎉", type="primary", on_click=celebrate, args=("grand",), key="celebrate_again")
    h.render(f'<div class="footer">Made with all my love, for you — {h.esc(config.YOUR_NAME)} 💗</div>')
    st.button("↺ Start from the beginning", type="tertiary", on_click=start_over, key="start_over")


def music_dock() -> None:
    """A mini player pinned to the bottom of the screen that starts the song on its own.

    It sits in a fixed slot at the top of the script, so it is never re-mounted and
    the song keeps playing while she clicks through the chapters.
    """
    audio = APP_DIR / config.AUDIO_FILE if config.AUDIO_FILE else None
    if not (audio and audio.is_file()):
        return
    with st.container(key="music_dock"):
        h.render(f'<div class="dock-label">🎵 {h.esc(config.SONG_TITLE)}</div>')
        try:
            st.audio(str(audio), autoplay=True, loop=True)
        except Exception:
            st.caption("The song couldn't be loaded — check AUDIO_FILE in config.py.")
            return
        if hasattr(st, "iframe"):  # Streamlit 1.5x+
            st.iframe(h.AUTOPLAY_HELPER, height=1)
        else:
            components.html(h.AUTOPLAY_HELPER, height=1)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

# These always render in the same order, so their slots never shift.
h.render(h.css(THEME) + '<div class="zero-gap"></div>')
h.render(h.background_html(THEME))
h.render(h.effects_html(state.fx, state.fx_id, THEME))
music_dock()

if not state.opened:
    welcome_screen()
else:
    journey_intro()
    # Each chapter lives in its own container so one chapter changing size
    # never re-mounts (and replays) the chapters below it.
    for section in (cake_section, letter_section, gift_section, wishes_section, countdown_section, finale_section):
        with st.container():
            section()
