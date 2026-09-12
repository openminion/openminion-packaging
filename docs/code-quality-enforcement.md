# Code-quality enforcement

The repository has one local aggregate gate:

```bash
make check
```

It runs:

```bash
python3.11 -m ruff format --check packaging tests
python3.11 -m ruff check packaging tests
python3.11 -m unittest discover -s tests -p 'test_*.py'
actionlint
```

The manual `Prototype` workflow adds native macOS, Linux, and Windows build
coverage. A local check proves repository logic and workflow shape; it does not
replace native target evidence.

Generated artifacts belong in ignored `dist/` and `wheel/` directories. Build
or workflow changes must keep the root documentation, source-tree owner map,
and testing guidance current.
