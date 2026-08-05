"""
Clean old demo data and keep only real AI-generated cases
"""

import sys
sys.path.insert(0, 'src')

import sqlite3

def clean_knowledge_base():
    """Remove old hardcoded demo data"""

    print("=" * 80)
    print("Cleaning Knowledge Base")
    print("=" * 80)
    print()

    conn = sqlite3.connect("formulation_knowledge.db")
    cursor = conn.cursor()

    # Find and delete the old demo session (demo_session_001)
    cursor.execute("SELECT session_id FROM sessions WHERE session_id LIKE 'demo_session_%'")
    old_sessions = cursor.fetchall()

    print(f"Found {len(old_sessions)} old demo sessions to remove")

    for (session_id,) in old_sessions:
        if session_id.startswith("demo_session_") and not session_id.startswith("demo_real_"):
            print(f"  Removing: {session_id}")

            # Delete messages
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

            # Get drug analyses
            cursor.execute("SELECT id FROM drug_analyses WHERE session_id = ?", (session_id,))
            analysis_ids = cursor.fetchall()

            for (analysis_id,) in analysis_ids:
                # Delete tool calls
                cursor.execute("DELETE FROM tool_calls WHERE drug_analysis_id = ?", (analysis_id,))
                # Delete properties
                cursor.execute("DELETE FROM properties WHERE drug_analysis_id = ?", (analysis_id,))
                # Delete strategies
                cursor.execute("DELETE FROM formulation_strategies WHERE drug_analysis_id = ?", (analysis_id,))
                # Delete hypotheses
                cursor.execute("DELETE FROM hypotheses WHERE drug_analysis_id = ?", (analysis_id,))

            # Delete drug analyses
            cursor.execute("DELETE FROM drug_analyses WHERE session_id = ?", (session_id,))

            # Delete session
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    conn.commit()

    # Show final stats
    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM drug_analyses")
    total_analyses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_calls")
    total_tool_calls = cursor.fetchone()[0]

    print()
    print("=" * 80)
    print("Cleanup Complete")
    print("=" * 80)
    print(f"Remaining sessions: {total_sessions}")
    print(f"Remaining messages: {total_messages}")
    print(f"Remaining analyses: {total_analyses}")
    print(f"Remaining tool calls: {total_tool_calls}")
    print()
    print("✅ Only real AI-generated demo cases remain!")

    conn.close()

if __name__ == "__main__":
    clean_knowledge_base()
