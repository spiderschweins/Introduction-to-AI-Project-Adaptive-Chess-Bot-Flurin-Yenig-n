# Documentation

This folder contains additional documentation for the Adaptive Chess Bot project.

## Contents

- [Architecture Overview](#architecture-overview)
- [API Documentation](#api-documentation)
- [Algorithm Details](#algorithm-details)

## Architecture Overview

```
┌─────────────────┐     HTTP      ┌─────────────────┐
│   Streamlit     │◄────────────►│    FastAPI      │
│   Frontend      │    REST API   │    Backend      │
│   (app.py)      │              │    (api.py)     │
└─────────────────┘              └────────┬────────┘
                                          │
                                          │ UCI Protocol
                                          ▼
                                 ┌─────────────────┐
                                 │   Stockfish     │
                                 │   Chess Engine  │
                                 └─────────────────┘
```

## API Documentation

See the main README.md for API endpoints, or visit `/docs` when running the server.

## Algorithm Details

### ELO Estimation (Power-Law Formula)

```
ELO = 323422 × (ACPL ^ -1.2305)
```

This formula was derived from empirical analysis of chess games correlating Average Centipawn Loss (ACPL) with known player ratings.

### Adaptive Depth Algorithm

The bot adjusts its search depth based on the player's estimated ELO:

| ELO Range | Depth | Rationale |
|-----------|-------|-----------|
| < 2000 | 1 | Beginner-friendly |
| 2000-2199 | 2 | Club player challenge |
| 2200-2349 | 3 | Advanced amateur |
| 2350-2499 | 4 | Expert level |
| 2500-2649 | 5 | Master level |
| 2650-2749 | 6 | Grandmaster |
| 2750-2899 | 7 | Super GM |
| ≥ 2900 | 8 | Maximum strength |

### Centipawn Loss Calculation

For each human move:
1. Analyze position BEFORE the move at depth 8
2. Get evaluation of the best move
3. Get evaluation of the played move
4. CPL = Best move eval - Played move eval

This measures how much "value" was lost by not playing the optimal move.
