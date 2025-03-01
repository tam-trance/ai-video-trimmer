import json
import os


def save_json(data, filename):
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(filename):
    """Load data from a JSON file.

    Args:
        filename: Path to the JSON file to load

    Returns:
        The data loaded from the JSON file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)
