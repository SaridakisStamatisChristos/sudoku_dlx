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
