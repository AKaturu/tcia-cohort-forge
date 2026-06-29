# Contributing

Contributions are welcome when they keep the project reproducible and safe for public data workflows.

## Local Setup

```bash
git clone https://github.com/AKaturu/tcia-cohort-forge.git
cd tcia-cohort-forge
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

## Guidelines

- Use public, synthetic, or properly de-identified examples only.
- Add or update tests for behavior changes.
- Keep public documentation clear about evidence status and limitations.
- Do not add credentials, private manifests, institutional exports, or protected health information.
