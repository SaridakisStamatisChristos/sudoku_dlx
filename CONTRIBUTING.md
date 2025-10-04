# Contributing

Thanks for your interest!

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest -q
```

## PR checklist

* Tests added/updated
* ruff & black pass
* CI green

## License

By contributing you agree your code is MIT-licensed under this repository.
