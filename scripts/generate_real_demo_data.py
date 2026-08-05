"""
Generate Real Demo Data with Actual AI Responses

This script calls the real AI system to generate authentic demo cases
instead of using hardcoded text.
"""

import sys
sys.path.insert(0, 'src')

from formulation_os.knowledge_base.database import KnowledgeBaseDB
from formulation_os.agent.conversation_memory import ConversationMemory
from formulation_os.agent.unified_llm_manager import UnifiedLLMManager
from formulation_os.agent.evidence_manager import EvidenceManager
import os
import uuid
from pathlib import Path

# Try to read API keys from secrets.toml
def get_api_key(key_name):
    """Try environment first, then secrets.toml"""
    env_value = os.environ.get(key_name)
    if env_value:
        return env_value

    # Try reading from .streamlit/secrets.toml
    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        import toml
        try:
            secrets = toml.load(secrets_path)
            return secrets.get(key_name)
        except:
            pass
    return None

GPT_API_KEY = get_api_key("GPT_API_KEY")
CLAUDE_API_KEY = get_api_key("CLAUDE_API_KEY")
MINIMAX_API_KEY = get_api_key("MINIMAX_API_KEY")

# Also get base URLs
GPT_BASE_URL = get_api_key("GPT_BASE_URL") or "https://api.openai.com/v1"
CLAUDE_BASE_URL = get_api_key("CLAUDE_BASE_URL") or "https://api.anthropic.com"
MINIMAX_BASE_URL = get_api_key("MINIMAX_BASE_URL") or "https://api.minimaxi.com/v1"

def generate_real_demo_data():
    """Generate demo data using real AI calls"""

    print("=" * 80)
    print("Generating Real Demo Data with AI")
    print("=" * 80)
    print()

    # Check API keys
    if not (GPT_API_KEY or CLAUDE_API_KEY or MINIMAX_API_KEY):
        print("❌ ERROR: No API key found!")
        print("Set GPT_API_KEY, CLAUDE_API_KEY, or MINIMAX_API_KEY environment variable")
        return

    model = "gpt-4o" if GPT_API_KEY else "claude-3-5-sonnet-20241022" if CLAUDE_API_KEY else "MiniMax-M3"
    print(f"Using model: {model}")
    print(f"Using base URL: {GPT_BASE_URL if GPT_API_KEY else CLAUDE_BASE_URL if CLAUDE_API_KEY else MINIMAX_BASE_URL}")
    print()

    # Initialize components
    kb = KnowledgeBaseDB()
    demo_session_id = f"demo_real_{uuid.uuid4().hex[:8]}"
    kb.create_session(demo_session_id)

    memory = ConversationMemory()
    evidence_manager = EvidenceManager()

    llm_manager = UnifiedLLMManager(
        memory=memory,
        openai_api_key=GPT_API_KEY,
        anthropic_api_key=CLAUDE_API_KEY,
        minimax_api_key=MINIMAX_API_KEY,
        openai_base_url=GPT_BASE_URL,
        anthropic_base_url=CLAUDE_BASE_URL,
        minimax_base_url=MINIMAX_BASE_URL,
        evidence_manager=evidence_manager
    )

    # Demo cases
    demo_queries = [
        {
            "name": "Ibuprofen",
            "query": "Analyze Ibuprofen formulation challenges. SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O. It's a BCS II drug, dose is 400mg. Recommend suitable solubility enhancement strategies.",
            "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
            "dosage_form": "Oral tablet"
        },
        {
            "name": "Paclitaxel",
            "query": "Paclitaxel has extremely poor solubility (BCS IV, MW=853 Da). What formulation approaches would work best? SMILES: CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)OC(=O)c5ccccc5)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c6ccccc6)c7ccccc7)O)(C)C",
            "smiles": "CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)OC(=O)c5ccccc5)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c6ccccc6)c7ccccc7)O)(C)C",
            "dosage_form": "Injectable"
        },
        {
            "name": "Celecoxib",
            "query": "Celecoxib is a BCS II drug (MW=381 Da, LogP~3.5). What solid dispersion polymer would you recommend? SMILES: Cc1ccc(cc1)c2cc(nn2c3ccc(cc3)S(=O)(=O)N)C(F)(F)F",
            "smiles": "Cc1ccc(cc1)c2cc(nn2c3ccc(cc3)S(=O)(=O)N)C(F)(F)F",
            "dosage_form": "Oral capsule"
        }
    ]

    for i, case in enumerate(demo_queries, 1):
        print(f"\n{'='*80}")
        print(f"Generating Case {i}: {case['name']}")
        print(f"{'='*80}")

        try:
            # Save user message
            kb.save_message(demo_session_id, "user", case['query'])
            print(f"Query: {case['query'][:80]}...")

            # Generate AI response
            print("🤖 Calling AI...")
            resp, tool_calls, _, _ = llm_manager.generate_with_tools_loop(
                user_query=case['query'],
                model=model,
                max_iterations=5
            )

            # Save drug analysis
            drug_analysis_id = kb.save_drug_analysis(
                demo_session_id,
                case['name'],
                case['smiles'],
                case['dosage_form']
            )

            # Save assistant response
            kb.save_message(demo_session_id, "assistant", resp, model_used=model)

            # Save tool calls if any
            if tool_calls:
                print(f"✓ Tool calls: {len(tool_calls)}")
                for tc in tool_calls:
                    kb.save_tool_call(
                        drug_analysis_id,
                        tc.get('tool_name', 'unknown'),
                        tc.get('module', 'unknown'),
                        tc.get('input', {}),
                        tc.get('output', {})
                    )

            print(f"✅ Generated {len(resp)} chars of response")

        except Exception as e:
            print(f"❌ ERROR generating {case['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Get final statistics
    print()
    print("=" * 80)
    print("Demo Data Generation Complete")
    print("=" * 80)
    stats = kb.get_statistics()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total analyses: {stats['total_drug_analyses']}")
    print(f"Unique drugs: {stats['unique_drugs']}")
    print(f"Total messages: {stats['total_messages']}")
    print(f"Tool calls: {stats['total_tool_calls']}")
    print()
    print("✅ Knowledge Base now contains REAL AI-generated demo cases!")
    print("🌐 Start Streamlit: streamlit run FormulationOS_Enterprise.py")

    kb.close()


if __name__ == "__main__":
    generate_real_demo_data()
