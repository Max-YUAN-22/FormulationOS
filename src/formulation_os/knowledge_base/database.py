"""Knowledge Base Storage for FormulationOS

Records all interactions for future model training:
- User queries
- AI responses
- Tool calls and results
- Drug properties analyzed
- Formulation strategies evaluated
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class KnowledgeBaseDB:
    """SQLite database for storing FormulationOS interactions"""

    def __init__(self, db_path: str = "formulation_knowledge.db"):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Sessions table - tracks each user session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                total_analyses INTEGER DEFAULT 0
            )
        """)

        # Messages table - all user-assistant exchanges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                role TEXT,  -- 'user' or 'assistant'
                content TEXT,
                model_used TEXT,  -- which AI model generated this
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Drug analyses table - every drug analyzed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drug_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                drug_name TEXT,
                smiles TEXT,
                dosage_form TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Tool calls table - PreformulationAI/FormulationAI calls
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_analysis_id INTEGER,
                timestamp TIMESTAMP,
                tool_name TEXT,  -- 'PreformulationAI', 'FormulationAI'
                module TEXT,  -- 'fundamentals', 'solid_dispersion', etc.
                input_params TEXT,  -- JSON
                output_result TEXT,  -- JSON
                FOREIGN KEY (drug_analysis_id) REFERENCES drug_analyses(id)
            )
        """)

        # Properties table - computed physicochemical properties
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_analysis_id INTEGER,
                property_name TEXT,  -- 'logP', 'logS', 'BCS_class', etc.
                property_value TEXT,  -- Can be number or string
                confidence REAL,
                source_tool TEXT,  -- Which tool computed this
                FOREIGN KEY (drug_analysis_id) REFERENCES drug_analyses(id)
            )
        """)

        # Formulation strategies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formulation_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_analysis_id INTEGER,
                strategy_type TEXT,  -- 'solid_dispersion', 'nanocrystal', etc.
                prediction_result TEXT,  -- JSON with detailed results
                recommendation TEXT,  -- AI's recommendation text
                FOREIGN KEY (drug_analysis_id) REFERENCES drug_analyses(id)
            )
        """)

        # Hypotheses table - AI-generated scientific hypotheses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_analysis_id INTEGER,
                timestamp TIMESTAMP,
                hypothesis_text TEXT,
                evidence TEXT,  -- JSON array of supporting evidence
                confidence_score REAL,
                FOREIGN KEY (drug_analysis_id) REFERENCES drug_analyses(id)
            )
        """)

        self.conn.commit()

    def create_session(self, session_id: str) -> None:
        """Start a new session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_id, start_time)
            VALUES (?, ?)
        """, (session_id, datetime.now()))
        self.conn.commit()

    def save_message(self, session_id: str, role: str, content: str,
                     model_used: str = None) -> int:
        """Save a message to database

        Returns:
            message_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, timestamp, role, content, model_used)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), role, content, model_used))

        # Update session message count
        cursor.execute("""
            UPDATE sessions
            SET total_messages = total_messages + 1
            WHERE session_id = ?
        """, (session_id,))

        self.conn.commit()
        return cursor.lastrowid

    def save_drug_analysis(self, session_id: str, drug_name: str,
                          smiles: str = None, dosage_form: str = None) -> int:
        """Save a new drug analysis

        Returns:
            drug_analysis_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO drug_analyses (session_id, timestamp, drug_name, smiles, dosage_form)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), drug_name, smiles, dosage_form))

        # Update session analysis count
        cursor.execute("""
            UPDATE sessions
            SET total_analyses = total_analyses + 1
            WHERE session_id = ?
        """, (session_id,))

        self.conn.commit()
        return cursor.lastrowid

    def save_tool_call(self, drug_analysis_id: int, tool_name: str,
                       module: str, input_params: Dict, output_result: Dict) -> int:
        """Save a tool call (PreformulationAI/FormulationAI)

        Returns:
            tool_call_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tool_calls (drug_analysis_id, timestamp, tool_name, module,
                                   input_params, output_result)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            drug_analysis_id,
            datetime.now(),
            tool_name,
            module,
            json.dumps(input_params),
            json.dumps(output_result)
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_property(self, drug_analysis_id: int, property_name: str,
                     property_value: Any, confidence: float = None,
                     source_tool: str = None) -> int:
        """Save a computed property

        Returns:
            property_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO properties (drug_analysis_id, property_name, property_value,
                                  confidence, source_tool)
            VALUES (?, ?, ?, ?, ?)
        """, (drug_analysis_id, property_name, str(property_value), confidence, source_tool))
        self.conn.commit()
        return cursor.lastrowid

    def save_formulation_strategy(self, drug_analysis_id: int, strategy_type: str,
                                  prediction_result: Dict, recommendation: str = None) -> int:
        """Save a formulation strategy evaluation

        Returns:
            strategy_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO formulation_strategies (drug_analysis_id, strategy_type,
                                              prediction_result, recommendation)
            VALUES (?, ?, ?, ?)
        """, (drug_analysis_id, strategy_type, json.dumps(prediction_result), recommendation))
        self.conn.commit()
        return cursor.lastrowid

    def save_hypothesis(self, drug_analysis_id: int, hypothesis_text: str,
                       evidence: List[str] = None, confidence_score: float = None) -> int:
        """Save an AI-generated hypothesis

        Returns:
            hypothesis_id
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO hypotheses (drug_analysis_id, timestamp, hypothesis_text,
                                  evidence, confidence_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            drug_analysis_id,
            datetime.now(),
            hypothesis_text,
            json.dumps(evidence or []),
            confidence_score
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_training_dataset(self, limit: int = None) -> List[Dict[str, Any]]:
        """Export all data for model training

        Returns list of training examples with structure:
        {
            "drug_name": "Ibuprofen",
            "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
            "user_query": "分析布洛芬的制剂挑战",
            "properties": {"logP": 3.97, "logS": -3.97, ...},
            "tool_calls": [...],
            "formulation_strategies": [...],
            "ai_response": "...",
            "hypotheses": [...]
        }
        """
        cursor = self.conn.cursor()

        # Get all drug analyses with related data
        query = """
            SELECT
                da.id as analysis_id,
                da.drug_name,
                da.smiles,
                da.dosage_form,
                da.timestamp
            FROM drug_analyses da
            ORDER BY da.timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        analyses = cursor.fetchall()

        training_data = []

        for analysis in analyses:
            analysis_id = analysis[0]

            # Get user query (first user message before this analysis)
            cursor.execute("""
                SELECT content FROM messages
                WHERE session_id = (
                    SELECT session_id FROM drug_analyses WHERE id = ?
                )
                AND role = 'user'
                AND timestamp <= (SELECT timestamp FROM drug_analyses WHERE id = ?)
                ORDER BY timestamp DESC LIMIT 1
            """, (analysis_id, analysis_id))
            user_query_row = cursor.fetchone()
            user_query = user_query_row[0] if user_query_row else ""

            # Get AI response
            cursor.execute("""
                SELECT content FROM messages
                WHERE session_id = (
                    SELECT session_id FROM drug_analyses WHERE id = ?
                )
                AND role = 'assistant'
                AND timestamp >= (SELECT timestamp FROM drug_analyses WHERE id = ?)
                ORDER BY timestamp ASC LIMIT 1
            """, (analysis_id, analysis_id))
            ai_response_row = cursor.fetchone()
            ai_response = ai_response_row[0] if ai_response_row else ""

            # Get all properties
            cursor.execute("""
                SELECT property_name, property_value, confidence, source_tool
                FROM properties WHERE drug_analysis_id = ?
            """, (analysis_id,))
            properties = {
                row[0]: {"value": row[1], "confidence": row[2], "source": row[3]}
                for row in cursor.fetchall()
            }

            # Get all tool calls
            cursor.execute("""
                SELECT tool_name, module, input_params, output_result
                FROM tool_calls WHERE drug_analysis_id = ?
            """, (analysis_id,))
            tool_calls = [
                {
                    "tool": row[0],
                    "module": row[1],
                    "input": json.loads(row[2]),
                    "output": json.loads(row[3])
                }
                for row in cursor.fetchall()
            ]

            # Get formulation strategies
            cursor.execute("""
                SELECT strategy_type, prediction_result, recommendation
                FROM formulation_strategies WHERE drug_analysis_id = ?
            """, (analysis_id,))
            strategies = [
                {
                    "type": row[0],
                    "result": json.loads(row[1]),
                    "recommendation": row[2]
                }
                for row in cursor.fetchall()
            ]

            # Get hypotheses
            cursor.execute("""
                SELECT hypothesis_text, evidence, confidence_score
                FROM hypotheses WHERE drug_analysis_id = ?
            """, (analysis_id,))
            hypotheses = [
                {
                    "text": row[0],
                    "evidence": json.loads(row[1]),
                    "confidence": row[2]
                }
                for row in cursor.fetchall()
            ]

            training_data.append({
                "drug_name": analysis[1],
                "smiles": analysis[2],
                "dosage_form": analysis[3],
                "timestamp": analysis[4],
                "user_query": user_query,
                "ai_response": ai_response,
                "properties": properties,
                "tool_calls": tool_calls,
                "formulation_strategies": strategies,
                "hypotheses": hypotheses
            })

        return training_data

    def export_to_json(self, output_path: str, limit: int = None) -> None:
        """Export training dataset to JSON file"""
        data = self.get_training_dataset(limit=limit)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        cursor = self.conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats['total_sessions'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM drug_analyses")
        stats['total_drug_analyses'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tool_calls")
        stats['total_tool_calls'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT drug_name) FROM drug_analyses")
        stats['unique_drugs'] = cursor.fetchone()[0]

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()
