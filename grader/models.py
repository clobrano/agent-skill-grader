"""Data models for evaluation items."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EvaluationConfig:
    """Top-level configuration for evaluation file."""

    agent_binary: Optional[str] = None
    model: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate field types and values."""
        if self.agent_binary is not None and not isinstance(self.agent_binary, str):
            raise TypeError(f"agent_binary must be str or None, got {type(self.agent_binary)}")
        if self.model is not None and not isinstance(self.model, str):
            raise TypeError(f"model must be str or None, got {type(self.model)}")

        # Validate non-empty strings
        if self.model is not None and not self.model.strip():
            raise ValueError("model cannot be empty or whitespace-only")


@dataclass
class EvaluationItem:
    """Single evaluation item with prompt, answer, and score."""

    prompt: str
    golden_answer: str
    score: float
    tokens: int
    prompt_file: Optional[str] = None
    golden_answer_file: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate field types and ranges."""
        if not isinstance(self.prompt, str):
            raise TypeError(f"prompt must be str, got {type(self.prompt)}")
        if not isinstance(self.golden_answer, str):
            raise TypeError(f"golden_answer must be str, got {type(self.golden_answer)}")
        if not isinstance(self.score, (int, float)):
            raise TypeError(f"score must be numeric, got {type(self.score)}")
        if not isinstance(self.tokens, int):
            raise TypeError(f"tokens must be int, got {type(self.tokens)}")

        if self.score < 0 or self.score > 1:
            raise ValueError(f"score must be between 0 and 1, got {self.score}")
        if self.tokens < 0:
            raise ValueError(f"tokens must be non-negative, got {self.tokens}")

        # Validate optional file references
        if self.prompt_file is not None and not isinstance(self.prompt_file, str):
            raise TypeError(f"prompt_file must be str or None, got {type(self.prompt_file)}")
        if self.golden_answer_file is not None and not isinstance(self.golden_answer_file, str):
            raise TypeError(f"golden_answer_file must be str or None, got {type(self.golden_answer_file)}")


@dataclass
class EvaluationDataset:
    """Collection of evaluation items."""

    items: List[EvaluationItem]
    config: Optional[EvaluationConfig] = None

    def __len__(self) -> int:
        """Return number of items."""
        return len(self.items)

    def __getitem__(self, index: int) -> EvaluationItem:
        """Get item by index."""
        return self.items[index]

    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)
