import streamlit as st
import requests
import pandas as pd
import os
import chess
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from streamlit.components.v1 import html
from chess.svg import board

API_URL = os.getenv("CHESSBOT_API_URL", "http://127.0.0.1:8000")

def _render_board(fen: str) -> None:
    svg = board(chess.Board(fen), size=420)
    html(svg, height=440)

def _get_legal_moves(fen: str) -> list[str]:
    b = chess.Board(fen)
    return [b.san(m) + f" ({m.uci()})" for m in b.legal_moves]

st.set_page_config(page_title="Adaptive Chess Bot", page_icon="♟️", layout="wide")
st.title("♟️ Adaptive Chess Bot")

with st.sidebar:
    session_id = st.text_input("Session ID", "demo")
    if st.button("New Session"):
        resp = requests.post(f"{API_URL}/session", json={"session_id": session_id, "depth": 4})
        if resp.status_code == 200:
            st.success("Session created")
            st.rerun()
        else:
            st.error(resp.text)

if session_id:
    resp = requests.get(f"{API_URL}/session/{session_id}")
    if resp.status_code == 200:
        data = resp.json()
        
        # Show current bot depth (adaptive) in sidebar
        with st.sidebar:
            st.metric("Bot Depth (Adaptive)", data['depth'])
            st.metric("Estimated ELO", data['strength'][0])
            avg_cpl = sum(data['avg_losses']) / len(data['avg_losses']) if data['avg_losses'] else 0
            st.metric("Avg Centipawn Loss", f"{avg_cpl:.1f}")
            
            # Show legal moves button
            if data['turn'] == 'white':
                with st.expander("Show Legal Moves"):
                    b = chess.Board(data['fen'])
                    for m in b.legal_moves:
                        san = b.san(m)
                        st.write(f"{san}:")
                        st.code(m.uci(), language=None)
        
        # Two-column layout: board on left, chart on right
        left_col, right_col = st.columns([3, 2], gap="large")
        
        with left_col:
            st.write(f"**Status:** {data['status']}")
            _render_board(data['fen'])
            st.write(f"**Moves:** {' '.join(data['moves'])}")
            st.write(f"**{data['strength'][1]}**")
            
            # Move input form (only show on white's turn)
            if data['turn'] == 'white':
                with st.form("move_form", clear_on_submit=True):
                    move = st.text_input("Your Move (UCI)", placeholder="e.g., e2e4")
                    submitted = st.form_submit_button("Make Move")
                    if submitted and move:
                        resp = requests.post(f"{API_URL}/session/{session_id}/move", json={"move": move})
                        if resp.status_code == 200:
                            # Auto-trigger bot move after successful human move
                            bot_resp = requests.post(f"{API_URL}/session/{session_id}/bot")
                            st.rerun()
                        else:
                            st.error(resp.text)
            else:
                st.info("Bot is thinking...")
                # Auto-trigger bot move if it's black's turn
                bot_resp = requests.post(f"{API_URL}/session/{session_id}/bot")
                if bot_resp.status_code == 200:
                    st.rerun()
                else:
                    st.error(bot_resp.text)
        
        with right_col:
            st.subheader("Centipawn Loss per Move")
            st.caption("Lower is better – 0 means perfect play!")
            # Always show chart (empty if no moves yet)
            moves = range(1, len(data['avg_losses']) + 1) if data['avg_losses'] else []
            cpl_values = data['avg_losses'] if data['avg_losses'] else []
            
            fig, ax = plt.subplots(figsize=(6, 4))
            if cpl_values:
                ax.bar(moves, cpl_values, color='#4e79a7')
            ax.set_xlabel("Move")
            ax.set_ylabel("Centipawn Loss")
            ax.set_title("Your Move Quality")
            
            # Ensure x-axis shows at least 20 moves
            current_max = len(cpl_values) if cpl_values else 0
            ax.set_xlim(0.5, max(20.5, current_max + 0.5))
            ax.set_ylim(0, 200)  # Reasonable ACPL range
            
            # Integer ticks for x-axis
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            
            st.pyplot(fig)
    else:
        st.info("Start a new session from the sidebar to play!")

# Glossary section at the bottom
st.divider()
st.header("📖 Glossary")

with st.expander("**Centipawn (cp)**", expanded=False):
    st.markdown("""
A **centipawn** is 1/100th of a pawn's value. Chess engines measure position advantages in centipawns.

- **+100 cp** = You're up roughly one pawn
- **+300 cp** = You're up roughly one minor piece (bishop/knight)
- **0 cp** = Equal position

It's a standardized way to quantify how good or bad a position is.
""")

with st.expander("**Centipawn Loss (CPL)**", expanded=False):
    st.markdown("""
**Centipawn Loss** measures how much worse your move was compared to the best move.

```
CPL = Engine's best move eval − Your move's eval
```

- **CPL = 0**: You played the best move!
- **CPL = 50**: You lost about half a pawn of advantage
- **CPL = 300**: You blundered a piece worth of value

Lower is better—it means you're playing closer to perfect chess.
""")

with st.expander("**Average Centipawn Loss (ACPL)**", expanded=False):
    st.markdown("""
**ACPL** is your average centipawn loss across all moves in the game.

```
ACPL = Sum of all CPL values / Number of moves
```

It's the most common metric for measuring overall playing strength:
- **ACPL < 25**: Super Grandmaster level
- **ACPL 25-50**: Grandmaster/International Master
- **ACPL 50-100**: Club player
- **ACPL > 100**: Beginner
""")

with st.expander("**ELO Rating Estimation (Power-Law Formula)**", expanded=False):
    st.markdown("""
We estimate your ELO rating from ACPL using an empirical **power-law formula**:

```
ELO = 323422 × (ACPL ^ -1.2305)
```

This formula was derived by fitting real player data (ACPL vs. known ELO ratings). The relationship follows a power law because:
- Small improvements in ACPL at high levels require exponentially more skill
- Beginners can improve ACPL quickly; masters improve slowly

**Examples:**
| ACPL | Estimated ELO | Level |
|------|---------------|-------|
| 25 | ~2800 | World Champion |
| 50 | ~2100 | Expert |
| 75 | ~1600 | Club Player |
| 120 | ~1100 | Beginner |

The estimate is clamped between 400 and 2800 for reasonable bounds.
""")

with st.expander("**Search Depth**", expanded=False):
    st.markdown("""
**Search depth** is how many moves ahead the chess engine looks.

- **Depth 1**: Looks 1 move ahead (very weak)
- **Depth 8**: Looks 8 moves ahead (very strong)
- **Depth 20+**: Tournament-level engine analysis

Higher depth = stronger play, but takes more time. This bot uses **adaptive depth**—it adjusts based on your estimated ELO so you always face a fair challenge:

| Your ELO | Bot Depth |
|----------|-----------|
| < 2000 | 1 |
| 2000-2199 | 2 |
| 2200-2349 | 3 |
| 2350-2499 | 4 |
| 2500-2649 | 5 |
| 2650-2749 | 6 |
| 2750-2899 | 7 |
| ≥ 2900 | 8 |
""")
