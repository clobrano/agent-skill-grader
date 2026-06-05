"""YAML file writing with format preservation."""
from pathlib import Path

from ruamel.yaml import YAML

from grader.models import EvaluationDataset


def write_yaml(filepath: str, dataset: EvaluationDataset) -> None:
    """Write evaluation dataset to YAML file in-place.

    Updates existing YAML file while preserving formatting, field order,
    and comments where possible. Preserves file references if present.
    Includes top-level config fields (agent_binary, model) if present.

    Args:
        filepath: Path to YAML file to update.
        dataset: EvaluationDataset with items and optional config to write.

    Raises:
        FileNotFoundError: If target directory doesn't exist.
        IOError: If file cannot be written.
    """
    path = Path(filepath)

    # Verify parent directory exists
    if not path.parent.exists():
        raise FileNotFoundError(f"Directory does not exist: {path.parent}")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False

    # Build data structure
    data = {}

    # Add config fields if config is present
    if dataset.config is not None:
        if dataset.config.agent_binary is not None:
            data["agent_binary"] = dataset.config.agent_binary
        if dataset.config.model is not None:
            data["model"] = dataset.config.model

    # Build items list
    items_list = []
    for item in dataset.items:
        item_dict = {}

        # Include prompt (file reference if available, else inline content)
        if item.prompt_file:
            item_dict["prompt_file"] = item.prompt_file
        else:
            item_dict["prompt"] = item.prompt

        # Include golden_answer (file reference if available, else inline content)
        if item.golden_answer_file:
            item_dict["golden_answer_file"] = item.golden_answer_file
        else:
            item_dict["golden_answer"] = item.golden_answer

        # Add score and tokens at the end to preserve field order
        item_dict["score"] = item.score
        item_dict["tokens"] = item.tokens

        items_list.append(item_dict)

    data["items"] = items_list

    # Write to file
    with open(path, 'w') as f:
        yaml.dump(data, f)
