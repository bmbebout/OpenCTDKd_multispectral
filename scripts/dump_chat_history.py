"""Dump a Copilot chat session from session-store.db to a markdown file."""

import sqlite3
import sys
from pathlib import Path

SESSION_ID = "fdd55f13-2937-43f6-8249-9c2608e82937"
DB_PATH = Path.home() / "AppData/Roaming/Code/User/globalStorage/github.copilot-chat/session-store.db"
OUT_PATH = Path(__file__).parents[1] / "dev-notes" / "260817_chat_history_dump.md"


def main():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.cursor()

    cur.execute(
        "SELECT summary, created_at, updated_at FROM sessions WHERE id = ?",
        (SESSION_ID,),
    )
    row = cur.fetchone()
    if not row:
        print(f"Session {SESSION_ID} not found.", file=sys.stderr)
        sys.exit(1)

    summary, created_at, updated_at = row

    cur.execute(
        "SELECT turn_index, user_message, assistant_response, timestamp"
        " FROM turns WHERE session_id = ? ORDER BY turn_index",
        (SESSION_ID,),
    )
    turns = cur.fetchall()
    con.close()

    lines = [
        f"# Chat History: {summary}",
        f"",
        f"Session ID: `{SESSION_ID}`  ",
        f"Created: {created_at}  ",
        f"Updated: {updated_at}",
        f"",
    ]

    for idx, user_msg, assistant_msg, ts in turns:
        lines += [
            f"---",
            f"",
            f"## Turn {idx + 1} — {ts}",
            f"",
            f"**User:**",
            f"",
            user_msg or "_(no message)_",
            f"",
            f"**Assistant:**",
            f"",
            assistant_msg or "_(no response)_",
            f"",
        ]

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()
