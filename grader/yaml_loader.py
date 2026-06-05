"""YAML file loading and parsing."""
from pathlib import Path
from typing import Any, Dict, List, Optional

from ruamel.yaml import YAML

from grader.models import EvaluationDataset, EvaluationItem, EvaluationConfig
from grader.validator import validate_item_dict


def _read_file_content(filepath: str) -> str:
    """Read content from a file.

    Args:
        filepath: Path to file to read.

    Returns:
        File content as string.

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        raise FileNotFoundError(f"Cannot read file {filepath}: {e}")


def _resolve_item_content(item_dict: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Resolve prompt and golden_answer from files if specified.

    Reads external files for prompt_file and golden_answer_file fields,
    populating the corresponding prompt and golden_answer fields.

    Args:
        item_dict: Dictionary with item data (may contain *_file fields).
        item_index: Index of item (for error reporting).

    Returns:
        Dictionary with prompt and golden_answer populated (from files or inline).

    Raises:
        FileNotFoundError: If referenced files don't exist.
    """
    resolved = dict(item_dict)

    # Resolve prompt: file takes precedence over inline
    if "prompt_file" in item_dict:
        resolved["prompt"] = _read_file_content(item_dict["prompt_file"])

    # Resolve golden_answer: file takes precedence over inline
    if "golden_answer_file" in item_dict:
        resolved["golden_answer"] = _read_file_content(item_dict["golden_answer_file"])

    return resolved


def _extract_config(data: Dict[str, Any]) -> Optional[EvaluationConfig]:
    """Extract config from top-level YAML data.

    Args:
        data: Parsed YAML data dictionary.

    Returns:
        EvaluationConfig if config fields present, None otherwise.

    Raises:
        ValueError: If config validation fails.
    """
    agent_binary = data.get("agent_binary")
    model = data.get("model")

    # Return None if neither field is present
    if agent_binary is None and model is None:
        return None

    # Create config (validates fields)
    return EvaluationConfig(agent_binary=agent_binary, model=model)


def load_yaml(filepath: str) -> EvaluationDataset:
    """Load evaluation dataset from YAML file.

    Args:
        filepath: Path to YAML file.

    Returns:
        EvaluationDataset with parsed items and optional config.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If YAML structure is invalid.
        Exception: If YAML parsing fails.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    try:
        with open(path, 'r') as f:
            data = yaml.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse YAML: {e}")

    if data is None:
        data = {}

    if "items" not in data:
        raise KeyError("YAML must contain 'items' key")

    items_data = data["items"]
    if not isinstance(items_data, list):
        raise TypeError(f"'items' must be a list, got {type(items_data).__name__}")

    items = []
    for index, item_dict in enumerate(items_data):
        validated_dict = validate_item_dict(item_dict, item_index=index)
        # Resolve file contents
        resolved_dict = _resolve_item_content(validated_dict, item_index=index)

        item = EvaluationItem(
            prompt=resolved_dict["prompt"],
            golden_answer=resolved_dict["golden_answer"],
            score=resolved_dict["score"],
            tokens=resolved_dict["tokens"],
            prompt_file=validated_dict.get("prompt_file"),
            golden_answer_file=validated_dict.get("golden_answer_file")
        )
        items.append(item)

    # Extract config if present
    config = _extract_config(data)

    return EvaluationDataset(items=items, config=config)
