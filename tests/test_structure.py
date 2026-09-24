from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_expected_project_directories_exist() -> None:
    expected = ["configs", "data", "models", "notebooks", "scripts", "src"]
    assert all((ROOT / directory).is_dir() for directory in expected)


def test_example_parameters_include_seed() -> None:
    text = (ROOT / "configs" / "params_example.txt").read_text()
    assert any(line.strip().startswith("Seed") for line in text.splitlines())
