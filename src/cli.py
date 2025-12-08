#!/usr/bin/env python3
"""
Command-line interface for the Adaptive Chess Bot.

This CLI allows users to:
- Play chess against an adaptive bot in the terminal
- Analyze positions and get evaluations
- Estimate ELO from ACPL values
- Run the API server or UI

Usage:
    python -m src.cli play                    # Play a game in terminal
    python -m src.cli analyze --fen "..."     # Analyze a position
    python -m src.cli estimate-elo --acpl 50  # Estimate ELO from ACPL
    python -m src.cli server                  # Start the API server
    python -m src.cli ui                      # Start the Streamlit UI
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chess
import chess.engine

# Import our modules
from src.api import _estimate_elo, _adaptive_depth, _stockfish_path


def play_game(args):
    """
    Play an interactive chess game against the adaptive bot in the terminal.
    
    The bot adjusts its difficulty based on your Average Centipawn Loss (ACPL).
    """
    print("\n" + "="*60)
    print("♟️  ADAPTIVE CHESS BOT - Terminal Edition")
    print("="*60)
    print("\nYou play as WHITE. Enter moves in UCI format (e.g., e2e4)")
    print("Commands: 'quit' to exit, 'board' to show position, 'hint' for best move")
    print("="*60 + "\n")
    
    # Initialize
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(_stockfish_path())
    
    total_loss = 0
    num_moves = 0
    current_depth = args.initial_depth
    
    try:
        while not board.is_game_over():
            # Display board
            print(f"\n{board}\n")
            print(f"FEN: {board.fen()}")
            
            if board.turn == chess.WHITE:
                # Player's turn
                print(f"\n📊 Stats: ACPL={total_loss/max(1,num_moves):.1f}, "
                      f"Est. ELO={_estimate_elo(total_loss/max(1,num_moves)) if num_moves > 0 else 'N/A'}, "
                      f"Bot Depth={current_depth}")
                
                while True:
                    move_input = input("\nYour move (WHITE): ").strip().lower()
                    
                    if move_input == 'quit':
                        print("\nThanks for playing!")
                        return
                    
                    if move_input == 'board':
                        print(f"\n{board}")
                        continue
                    
                    if move_input == 'hint':
                        hint = engine.play(board, chess.engine.Limit(depth=8))
                        print(f"💡 Hint: {hint.move.uci()} ({board.san(hint.move)})")
                        continue
                    
                    if move_input == 'legal':
                        legal = [f"{board.san(m)} ({m.uci()})" for m in board.legal_moves]
                        print(f"Legal moves: {', '.join(legal)}")
                        continue
                    
                    try:
                        move = chess.Move.from_uci(move_input)
                        if move not in board.legal_moves:
                            print("❌ Illegal move. Try again or type 'legal' to see legal moves.")
                            continue
                        
                        # Calculate CPL for this move
                        result = engine.play(board, chess.engine.Limit(depth=8))
                        best_move = result.move
                        
                        # Evaluate best move
                        board.push(best_move)
                        best_eval = engine.analyse(board, chess.engine.Limit(depth=8))["score"].relative.score(mate_score=10000)
                        board.pop()
                        
                        # Evaluate player's move
                        board.push(move)
                        played_eval = engine.analyse(board, chess.engine.Limit(depth=8))["score"].relative.score(mate_score=10000)
                        board.pop()
                        
                        # Calculate CPL
                        cpl = max(0, played_eval - best_eval)
                        total_loss += cpl
                        num_moves += 1
                        
                        # Update adaptive depth
                        acpl = total_loss / num_moves
                        estimated_elo = _estimate_elo(acpl)
                        current_depth = _adaptive_depth(estimated_elo)
                        
                        # Make the move
                        board.push(move)
                        
                        if cpl == 0:
                            print(f"✅ Perfect move! CPL: 0")
                        elif cpl < 20:
                            print(f"👍 Good move! CPL: {cpl}")
                        elif cpl < 50:
                            print(f"⚠️  Inaccuracy. CPL: {cpl}")
                        elif cpl < 100:
                            print(f"❌ Mistake! CPL: {cpl}")
                        else:
                            print(f"💀 Blunder! CPL: {cpl}")
                        
                        break
                        
                    except ValueError:
                        print("❌ Invalid format. Use UCI notation (e.g., e2e4)")
            
            else:
                # Bot's turn
                print(f"\n🤖 Bot thinking at depth {current_depth}...")
                result = engine.play(board, chess.engine.Limit(depth=current_depth))
                bot_move = result.move
                print(f"🤖 Bot plays: {bot_move.uci()} ({board.san(bot_move)})")
                board.push(bot_move)
        
        # Game over
        print(f"\n{board}\n")
        print("="*60)
        print(f"🏁 GAME OVER: {board.result()}")
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            print(f"   {winner} wins by checkmate!")
        elif board.is_stalemate():
            print("   Draw by stalemate.")
        elif board.is_insufficient_material():
            print("   Draw by insufficient material.")
        
        if num_moves > 0:
            final_acpl = total_loss / num_moves
            final_elo = _estimate_elo(final_acpl)
            print(f"\n📊 Final Stats:")
            print(f"   Moves played: {num_moves}")
            print(f"   Average CPL: {final_acpl:.1f}")
            print(f"   Estimated ELO: {final_elo}")
        print("="*60)
        
    finally:
        engine.quit()


def analyze_position(args):
    """
    Analyze a chess position given in FEN notation.
    """
    print("\n" + "="*60)
    print("♟️  POSITION ANALYSIS")
    print("="*60)
    
    try:
        board = chess.Board(args.fen)
    except ValueError as e:
        print(f"❌ Invalid FEN: {e}")
        sys.exit(1)
    
    print(f"\n{board}\n")
    print(f"FEN: {args.fen}")
    print(f"Turn: {'White' if board.turn else 'Black'}")
    
    engine = chess.engine.SimpleEngine.popen_uci(_stockfish_path())
    
    try:
        depth = args.depth
        print(f"\nAnalyzing at depth {depth}...")
        
        # Get best move
        result = engine.play(board, chess.engine.Limit(depth=depth))
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        
        score = info["score"].relative
        if score.is_mate():
            eval_str = f"Mate in {score.mate()}"
        else:
            cp = score.score()
            eval_str = f"{cp/100:+.2f}" if cp else "0.00"
        
        print(f"\n📊 Analysis Results:")
        print(f"   Best move: {result.move.uci()} ({board.san(result.move)})")
        print(f"   Evaluation: {eval_str}")
        print(f"   Depth: {depth}")
        
        # Show top 3 moves if requested
        if args.lines > 1:
            print(f"\n   Top {args.lines} moves:")
            info_multi = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=args.lines)
            for i, pv_info in enumerate(info_multi if isinstance(info_multi, list) else [info_multi]):
                pv = pv_info.get("pv", [])
                pv_score = pv_info["score"].relative
                if pv_score.is_mate():
                    pv_eval = f"M{pv_score.mate()}"
                else:
                    pv_eval = f"{pv_score.score()/100:+.2f}"
                if pv:
                    print(f"   {i+1}. {pv[0].uci()} ({board.san(pv[0])}) [{pv_eval}]")
        
    finally:
        engine.quit()
    
    print("="*60)


def estimate_elo_cmd(args):
    """
    Estimate ELO rating from an ACPL value.
    """
    acpl = args.acpl
    elo = _estimate_elo(acpl)
    depth = _adaptive_depth(elo)
    
    print("\n" + "="*60)
    print("♟️  ELO ESTIMATION")
    print("="*60)
    print(f"\n   Input ACPL: {acpl}")
    print(f"   Estimated ELO: {elo}")
    print(f"   Recommended Bot Depth: {depth}")
    print(f"\n   Formula: ELO = 323422 × ACPL^(-1.2305)")
    print("="*60)


def run_server(args):
    """
    Start the FastAPI backend server.
    """
    import uvicorn
    print("\n🚀 Starting Adaptive Chess Bot API server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs\n")
    
    uvicorn.run("src.api:app", host=args.host, port=args.port, reload=args.reload)


def run_ui(args):
    """
    Start the Streamlit frontend UI.
    """
    import subprocess
    print("\n🚀 Starting Adaptive Chess Bot UI...")
    print(f"   Port: {args.port}\n")
    
    ui_path = Path(__file__).parent / "app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(ui_path),
        "--server.port", str(args.port)
    ])


def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        prog="adaptive-chess-bot",
        description="Adaptive Chess Bot - An AI opponent that adjusts to your skill level",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli play                      # Play a game in terminal
  python -m src.cli play --depth 3            # Start with bot at depth 3
  python -m src.cli analyze --fen "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  python -m src.cli estimate-elo --acpl 50    # What ELO corresponds to 50 ACPL?
  python -m src.cli server --port 8000        # Start API server
  python -m src.cli ui --port 8501            # Start web UI
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Play command
    play_parser = subparsers.add_parser("play", help="Play a game against the adaptive bot")
    play_parser.add_argument(
        "--depth", "-d",
        type=int,
        default=4,
        dest="initial_depth",
        help="Initial bot depth (1-8, default: 4)"
    )
    play_parser.set_defaults(func=play_game)
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a chess position")
    analyze_parser.add_argument(
        "--fen", "-f",
        type=str,
        required=True,
        help="FEN string of the position to analyze"
    )
    analyze_parser.add_argument(
        "--depth", "-d",
        type=int,
        default=12,
        help="Analysis depth (default: 12)"
    )
    analyze_parser.add_argument(
        "--lines", "-l",
        type=int,
        default=1,
        help="Number of top moves to show (default: 1)"
    )
    analyze_parser.set_defaults(func=analyze_position)
    
    # Estimate ELO command
    elo_parser = subparsers.add_parser("estimate-elo", help="Estimate ELO from ACPL")
    elo_parser.add_argument(
        "--acpl", "-a",
        type=float,
        required=True,
        help="Average Centipawn Loss value"
    )
    elo_parser.set_defaults(func=estimate_elo_cmd)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument(
        "--host", "-H",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    server_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    server_parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="Enable auto-reload for development"
    )
    server_parser.set_defaults(func=run_server)
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit UI")
    ui_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8501,
        help="Port to bind to (default: 8501)"
    )
    ui_parser.set_defaults(func=run_ui)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Execute the appropriate function
    args.func(args)


if __name__ == "__main__":
    main()
