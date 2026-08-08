"""Test script for all FormulationOS local models.

Tests:
1. PreFormulationAI models (sklearn + PyTorch)
2. FormulationAI Decision Tree models
3. Solid Dispersion LightGBM model
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("FormulationOS Model Testing Suite")
print("=" * 80)

# Test drug: Ibuprofen
test_smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
test_drug_name = "Ibuprofen"

print(f"\nTest Drug: {test_drug_name}")
print(f"SMILES: {test_smiles}")
print()

# ============================================================================
# Test 1: PreFormulationAI
# ============================================================================
print("=" * 80)
print("Test 1: PreFormulationAI Models")
print("=" * 80)

try:
    from formulation_os.tools.builtins.preformulation_ai.model_loader import (
        check_models_available,
        predict_druglikeness,
        predict_oral_bioavailability,
        predict_injectable_feasibility,
        predict_solubility_class,
        predict_hygroscopicity,
        run_preformulation_suite,
    )

    # Check model availability
    print("\n1.1 Model Availability Check:")
    models_status = check_models_available()
    sklearn_count = sum(1 for k, v in models_status.items() if v and not k.endswith('.ckpt'))
    pytorch_count = sum(1 for k, v in models_status.items() if v and k.endswith('.ckpt'))

    print(f"  ✓ Scikit-learn models available: {sklearn_count}")
    print(f"  ✓ PyTorch models available: {pytorch_count}")

    # Test individual predictions
    print("\n1.2 Drug-likeness Prediction:")
    druglike = predict_druglikeness(test_smiles)
    print(f"  Result: {druglike['category']}")
    print(f"  Probability: {druglike['probability']:.2%}")

    print("\n1.3 Oral Bioavailability Prediction:")
    oral = predict_oral_bioavailability(test_smiles)
    print(f"  Result: {oral['category']}")
    print(f"  Probability: {oral['probability']:.2%}")

    print("\n1.4 Injectable Feasibility Prediction:")
    injectable = predict_injectable_feasibility(test_smiles)
    print(f"  Result: {injectable['category']}")
    print(f"  Probability: {injectable['probability']:.2%}")

    print("\n1.5 Solubility Classification:")
    solubility = predict_solubility_class(test_smiles)
    print(f"  Class: {solubility['solubility_class']}")
    print(f"  Confidence: {solubility['probability']:.2%}")

    print("\n1.6 Hygroscopicity Prediction:")
    hygro = predict_hygroscopicity(test_smiles)
    print(f"  Class: {hygro['hygroscopicity_class']}")

    print("\n1.7 Full Suite Test:")
    suite_results = run_preformulation_suite(test_smiles)
    print(f"  Success: {suite_results['success']}")
    print(f"  Summary:\n{suite_results['summary']}")

    print("\n✅ PreFormulationAI: PASSED")

except Exception as e:
    print(f"\n❌ PreFormulationAI: FAILED")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 2: FormulationAI
# ============================================================================
print("\n" + "=" * 80)
print("Test 2: FormulationAI Decision Tree Models")
print("=" * 80)

try:
    from formulation_os.tools.builtins.formulation_ai.model_loader import (
        check_models_available,
        predict_oral_formulation,
        predict_injectable_formulation,
    )

    # Check model availability
    print("\n2.1 Model Availability Check:")
    models_available = check_models_available()
    print(f"  Models available: {models_available}")

    if models_available:
        # Test oral formulation
        print("\n2.2 Oral Formulation Prediction:")
        oral_pred = predict_oral_formulation(test_smiles, bcs_class="II")
        print(f"  Strategy: {oral_pred['strategy']}")
        print(f"  Confidence: {oral_pred['confidence']:.2%}")
        print(f"  Level 1 Classification: {oral_pred['level1_classification']}")
        print(f"  Level 2 Classification: {oral_pred['level2_classification']}")

        # Test injectable formulation
        print("\n2.3 Injectable Formulation Prediction:")
        injectable_pred = predict_injectable_formulation(test_smiles)
        print(f"  Strategy: {injectable_pred['strategy']}")
        print(f"  Confidence: {injectable_pred['confidence']:.2%}")
        print(f"  Level 1 Classification: {injectable_pred['level1_classification']}")
        print(f"  Level 2 Classification: {injectable_pred['level2_classification']}")

        print("\n✅ FormulationAI: PASSED")
    else:
        print("\n⚠️  FormulationAI: Models not found")

except Exception as e:
    print(f"\n❌ FormulationAI: FAILED")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 3: Solid Dispersion
# ============================================================================
print("\n" + "=" * 80)
print("Test 3: Solid Dispersion LightGBM Model")
print("=" * 80)

try:
    from formulation_os.tools.builtins.solid_dispersion.model_loader import (
        check_model_available,
        predict_solid_dispersion,
        get_available_polymers,
        get_available_methods,
    )

    # Check model availability
    print("\n3.1 Model Availability Check:")
    model_available = check_model_available()
    print(f"  LightGBM model available: {model_available}")

    if model_available:
        # Show available options
        print("\n3.2 Available Options:")
        print(f"  Polymers: {', '.join(get_available_polymers())}")
        print(f"  Methods: {', '.join(get_available_methods())}")

        # Test prediction with different polymers
        print("\n3.3 Solid Dispersion Predictions:")

        for polymer in ["PVP K30", "HPMC-AS", "Soluplus"]:
            pred = predict_solid_dispersion(
                smiles=test_smiles,
                polymer=polymer,
                method="HME",
                drug_loading=15.0,
                temperature=170.0
            )
            print(f"\n  {polymer}:")
            print(f"    Solubility Enhancement: {pred['solubility_enhancement_fold']:.1f}x")
            print(f"    Stability Score: {pred['stability_score']:.2f}")
            print(f"    Confidence: {pred['confidence']:.2%}")
            print(f"    Recommended: {'Yes' if pred['recommended'] else 'No'}")

        print("\n✅ Solid Dispersion: PASSED")
    else:
        print("\n⚠️  Solid Dispersion: Model not found")

except Exception as e:
    print(f"\n❌ Solid Dispersion: FAILED")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 4: Backend Integration
# ============================================================================
print("\n" + "=" * 80)
print("Test 4: Backend Integration (Tool Interface)")
print("=" * 80)

try:
    from formulation_os.tools.builtins.preformulation_ai import backend as pf_backend
    from formulation_os.tools.builtins.formulation_ai import backend as f_backend

    print("\n4.1 PreFormulationAI Backend:")
    pf_result = pf_backend.run({
        "drug_name": test_drug_name,
        "smiles": test_smiles,
    })
    print(f"  Drug: {pf_result.get('drug_name')}")
    print(f"  Warnings: {len(pf_result.get('warnings', []))}")
    if 'MOCK' in str(pf_result.get('warnings', [])):
        print("  ⚠️  Using mock backend")
    else:
        print("  ✓ Using real models")

    print("\n4.2 FormulationAI Backend:")
    f_result = f_backend.run({
        "drug_name": test_drug_name,
        "smiles": test_smiles,
        "dosage_form": "tablet",
        "bcs_class": "II",
    })
    print(f"  Strategy: {f_result.get('recommended_strategy', 'N/A')}")
    print(f"  Confidence: {f_result.get('confidence', 0):.2%}")
    if 'MOCK' in str(f_result.get('warnings', [])):
        print("  ⚠️  Using mock backend")
    else:
        print("  ✓ Using real models")

    print("\n✅ Backend Integration: PASSED")

except Exception as e:
    print(f"\n❌ Backend Integration: FAILED")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
print("\nIf all tests passed, the models are ready for production use.")
print("If some tests showed warnings, check that all model files are in place.")
print()
