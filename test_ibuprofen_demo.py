"""
End-to-end test for Ibuprofen formulation analysis
Verify the complete reasoning chain: Tools → Evidence → Mechanisms → Hypotheses → Context → Validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from formulation_os.agent.conversation_memory import ConversationMemory
from formulation_os.agent.unified_llm_manager import UnifiedLLMManager
from formulation_os.agent.evidence_manager import EvidenceManager
from formulation_os.agent.hypothesis_ranker import HypothesisRanker
from formulation_os.agent.context_reasoner import DrugContext
import json
import os

# Configuration
GPT_API_KEY = "sk-rpuahfQDWzbqQKW0AbzGJpo7OMpftFRAaOsFzQUXqUXlMMNW"
GPT_BASE_URL = "https://www.cun.ai/v1"

def test_ibuprofen_reasoning_chain():
    """Test complete reasoning chain for Ibuprofen"""
    
    print("=" * 80)
    print("FormulationOS Scientific Reasoning Validation")
    print("Test Case: Ibuprofen Oral Bioavailability Enhancement")
    print("=" * 80)
    print()
    
    # Initialize components
    memory = ConversationMemory()
    evidence_manager = EvidenceManager()
    hypothesis_ranker = HypothesisRanker(evidence_manager=evidence_manager)
    
    llm_manager = UnifiedLLMManager(
        memory=memory,
        anthropic_api_key="",
        openai_api_key=GPT_API_KEY,
        minimax_api_key="",
        anthropic_base_url="",
        openai_base_url=GPT_BASE_URL,
        minimax_base_url="",
        evidence_manager=evidence_manager
    )
    
    # Test query
    query = """Analyze Ibuprofen formulation challenges.

SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O

Goal: Improve oral bioavailability"""
    
    print("📝 User Query:")
    print(query)
    print()
    print("-" * 80)
    print()
    
    # Generate response with tools
    print("🔬 Executing tool-based analysis...")
    print()
    
    try:
        response, tool_calls, input_tokens, output_tokens = llm_manager.generate_with_tools_loop(
            user_query=query,
            model="gpt-4o",
            max_iterations=5
        )
        
        print("✅ Analysis completed")
        print()
        print("=" * 80)
        print("PHASE 1: Tool Execution Summary")
        print("=" * 80)
        print()
        print(f"Total tools called: {len(tool_calls)}")
        print()
        
        for i, tc in enumerate(tool_calls, 1):
            print(f"{i}. {tc.get('name', 'unknown')}")
            if 'result' in tc:
                result = tc['result']
                if isinstance(result, dict):
                    # Extract key metrics
                    if 'LogP' in result:
                        print(f"   LogP: {result.get('LogP', 'N/A')}")
                    if 'LogS' in result:
                        print(f"   LogS: {result.get('LogS', 'N/A')}")
                    if 'BCS_class' in result:
                        print(f"   BCS: {result.get('BCS_class', 'N/A')}")
                    if 'stability_prediction' in result:
                        print(f"   Stability: {result.get('stability_prediction', 'N/A')}")
        print()
        
        print("=" * 80)
        print("PHASE 2: Evidence Collection")
        print("=" * 80)
        print()
        
        # Capture evidence from tool calls
        for tc in tool_calls:
            tool_name = tc.get('name', '')
            tool_result = tc.get('result', {})
            evidence_list = evidence_manager.capture_from_tool_call(tool_name, tool_result)
            
            for evidence in evidence_list:
                print(f"Evidence #{len(evidence_manager.evidence_pool)}")
                print(f"  Observation: {evidence.observation}")
                print(f"  Interpretation: {evidence.interpretation}")
                print(f"  Mechanism: {evidence.mechanism.value if evidence.mechanism else 'None'}")
                print(f"  Confidence: {evidence.confidence:.2f}")
                print()
        
        print(f"Total evidence collected: {len(evidence_manager.evidence_pool)}")
        print()
        
        print("=" * 80)
        print("PHASE 3: AI Response")
        print("=" * 80)
        print()
        print(response)
        print()
        
        print("=" * 80)
        print("PHASE 4: Validation")
        print("=" * 80)
        print()
        
        # Check if response follows hypothesis format
        has_hypothesis_format = "Hypothesis:" in response or "Evidence:" in response
        has_uncertainty = "Uncertainty:" in response or "unknown" in response.lower()
        has_validation = "Validation:" in response or "experiment" in response.lower()
        
        print("✓ Hypothesis format:", "✅" if has_hypothesis_format else "❌")
        print("✓ Uncertainty acknowledgment:", "✅" if has_uncertainty else "❌")
        print("✓ Validation plan:", "✅" if has_validation else "❌")
        print()
        
        # Save demo results
        demo_data = {
            "drug": "Ibuprofen",
            "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
            "query": query,
            "tool_calls": len(tool_calls),
            "evidence_count": len(evidence_manager.evidence_pool),
            "response": response,
            "tokens": {"input": input_tokens, "output": output_tokens}
        }
        
        with open("demo_ibuprofen.json", "w") as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        print("💾 Demo saved to: demo_ibuprofen.json")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ibuprofen_reasoning_chain()
    sys.exit(0 if success else 1)
