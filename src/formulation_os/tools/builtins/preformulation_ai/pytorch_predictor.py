"""PyTorch model predictor for PreFormulationAI.

Uses Chemprop models to predict physicochemical properties from SMILES.
These predictions are then used as features for downstream ML models.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import torch

# Global cache for loaded PyTorch models
_PYTORCH_MODEL_CACHE: dict[str, Any] = {}

# Find models directory
_MODELS_DIR = Path(__file__).parent / "models"

# Suppress PyTorch Lightning warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pytorch_lightning")


def _load_chemprop_model(model_name: str) -> Any:
    """Load a Chemprop PyTorch Lightning model from checkpoint.

    Args:
        model_name: Name of the model (e.g., 'logP', 'MP', 'Tg')

    Returns:
        Loaded Chemprop model in eval mode
    """
    if model_name in _PYTORCH_MODEL_CACHE:
        return _PYTORCH_MODEL_CACHE[model_name]

    model_path = _MODELS_DIR / f"{model_name}.ckpt"

    if not model_path.exists():
        raise FileNotFoundError(f"PyTorch model not found: {model_path}")

    try:
        from chemprop.models import MPNN

        # Load checkpoint with weights_only=False (required for Chemprop)
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'), weights_only=False)

        # Extract model from checkpoint
        if isinstance(checkpoint, dict):
            # PyTorch Lightning checkpoint format
            model = MPNN.load_from_checkpoint(model_path, map_location=torch.device('cpu'))
        else:
            # Direct model object
            model = checkpoint

        model.eval()

        _PYTORCH_MODEL_CACHE[model_name] = model
        return model

    except ImportError:
        raise ImportError(
            "Chemprop not installed. Run: pip install chemprop\n"
            "These PyTorch models require the Chemprop library for molecular property prediction."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load model {model_name}: {str(e)}")


def predict_single_property(smiles: str, model_name: str) -> float:
    """Predict a single physicochemical property from SMILES.

    Args:
        smiles: SMILES string
        model_name: Name of the property model (e.g., 'logP', 'MP')

    Returns:
        Predicted property value
    """
    model = _load_chemprop_model(model_name)

    try:
        from chemprop.data import MoleculeDatapoint, MoleculeDataset, build_dataloader

        # Create datapoint and dataset
        datapoint = MoleculeDatapoint.from_smi(smiles)
        dataset = MoleculeDataset([datapoint])

        # Build dataloader for proper batching
        dataloader = build_dataloader(dataset, batch_size=1, shuffle=False)

        # Get prediction from first batch
        with torch.no_grad():
            for batch in dataloader:
                # Correct API: pass batch components separately
                prediction = model(batch.bmg, batch.V_d, batch.X_d)

                # Extract scalar value
                if isinstance(prediction, torch.Tensor):
                    value = prediction.item() if prediction.numel() == 1 else prediction[0, 0].item()
                else:
                    value = float(prediction)

                return value

    except Exception as e:
        raise RuntimeError(f"Prediction failed for {model_name}: {str(e)}")


def predict_all_pytorch_properties(smiles: str) -> dict[str, float]:
    """Predict all available physicochemical properties using PyTorch models.

    Args:
        smiles: SMILES string

    Returns:
        Dictionary with predicted properties:
        - Density (g/cm³)
        - MP (melting point, °C)
        - Tg (glass transition temperature, °C)
        - logP (partition coefficient)
        - logD (distribution coefficient at pH 7.4)
        - A_pKa (acidic pKa)
        - B_pKa (basic pKa)
        - logS (solubility)
        - logPapp (apparent permeability)
        - Kinetic_Solubility_Pred (kinetic solubility)
    """
    # Available PyTorch models
    pytorch_models = [
        "density",
        "MP",
        "Tg",
        "logP",
        "logD",
        "A_pKa",
        "B_pKa",
        "logS",
        "logPapp",
        "kinetic_solubility",
    ]

    predictions = {}

    for model_name in pytorch_models:
        model_path = _MODELS_DIR / f"{model_name}.ckpt"

        if not model_path.exists():
            # Model file not available, skip
            predictions[model_name] = None
            continue

        try:
            value = predict_single_property(smiles, model_name)
            predictions[model_name] = value
        except Exception as e:
            print(f"Warning: Failed to predict {model_name}: {str(e)}")
            predictions[model_name] = None

    # Map to expected feature names (matching training data columns)
    feature_names = {
        "density": "Density",
        "MP": "MP",
        "Tg": "Tg",
        "logP": "logP",
        "logD": "logD",
        "A_pKa": "A_pKa",
        "B_pKa": "B_pKa",
        "logS": "logS",
        "logPapp": "logPapp",
        "kinetic_solubility": "Kinetic_Solubility_Pred",
    }

    result = {}
    for model_key, feature_name in feature_names.items():
        result[feature_name] = predictions.get(model_key)

    return result


def check_pytorch_models_available() -> dict[str, bool]:
    """Check which PyTorch models are available.

    Returns:
        Dictionary mapping model names to availability
    """
    pytorch_models = [
        "density",
        "MP",
        "Tg",
        "logP",
        "logD",
        "A_pKa",
        "B_pKa",
        "logS",
        "logPapp",
        "kinetic_solubility",
    ]

    availability = {}
    for model_name in pytorch_models:
        model_path = _MODELS_DIR / f"{model_name}.ckpt"
        availability[model_name] = model_path.exists()

    return availability


def predict_with_fallback(smiles: str, model_name: str, fallback_value: float = 0.0) -> float:
    """Predict property with fallback to default value if model unavailable.

    Args:
        smiles: SMILES string
        model_name: Name of the property model
        fallback_value: Default value if prediction fails

    Returns:
        Predicted value or fallback
    """
    try:
        return predict_single_property(smiles, model_name)
    except Exception:
        return fallback_value
