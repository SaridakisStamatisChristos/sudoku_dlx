# CLI Guide

Run `sudoku-dlx --help` for a full list.

<!-- core -->
## Solve
```bash
sudoku-dlx solve --grid "<81chars>" [--pretty] [--stats] [--trace out.json] [--crosscheck sat]
```

## Generate
```bash
sudoku-dlx gen --seed 123 --givens 30 [--minimal] [--symmetry none|rot180|mix] [--pretty]
```

## Rate
```bash
sudoku-dlx rate --grid "<81chars>"
```

## Check (analyze)
```bash
sudoku-dlx check --grid "<81chars>" [--json]
```

## Canonicalize
```bash
sudoku-dlx canon --grid "<81chars>"
```

## Explain (human steps)
```bash
sudoku-dlx explain --grid "<81chars>" [--json] [--max-steps 200]
```

## Batch tools
```bash
# Generate unique canonical puzzles
sudoku-dlx gen-batch --out puzzles.txt --count 1000 --givens 30 \
  --min-givens 28 --max-givens 40 --parallel 8

# Rate file (JSON lines)
sudoku-dlx rate-file --in puzzles.txt --json > scores.ndjson

# Stats with sampling & histogram CSV
sudoku-dlx stats-file --in puzzles.txt --limit 5000 --sample 1000 --json stats.json
```

<!-- extras -->
## Convert formats
```bash
# auto-detects txt/csv/jsonl by extension
sudoku-dlx convert --in puzzles.txt --out puzzles.csv
sudoku-dlx convert --in puzzles.csv --out puzzles.jsonl
```

## Explain (batch)
```bash
sudoku-dlx explain-file --in puzzles.txt --out steps.ndjson --max-steps 200
```

## Export to DIMACS CNF
```bash
sudoku-dlx to-cnf --grid "<81chars>" --out puzzle.cnf
```
