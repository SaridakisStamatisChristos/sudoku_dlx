# Batch & Datasets

## Generate many puzzles
```bash
sudoku-dlx gen-batch --out puzzles.txt --count 1000 --givens 30 \
  --min-givens 28 --max-givens 40 --parallel 8
```
Puzzles are written one per line in **canonical** form, de-duplicated.

## Rate a file
```bash
sudoku-dlx rate-file --in puzzles.txt --json > scores.ndjson
```

## Stats with sampling
```bash
sudoku-dlx stats-file --in puzzles.txt --limit 5000 --sample 1000 --json stats.json
```

## Dedupe a file
```bash
sudoku-dlx dedupe --in puzzles.txt --out unique.txt
```

## Convert between formats
Supported: txt (one 81-char per line), csv (column grid), jsonl/ndjson ({"grid": "..."} per line).
```bash
sudoku-dlx convert --in puzzles.txt --out puzzles.csv
sudoku-dlx convert --in puzzles.csv --out puzzles.jsonl
```

## Batch explain
Produce one JSON object per line with steps and progress:
```bash
sudoku-dlx explain-file --in puzzles.txt --out steps.ndjson --max-steps 200
```

## Export to CNF
```bash
sudoku-dlx to-cnf --grid "<81chars>" --out puzzle.cnf
```
