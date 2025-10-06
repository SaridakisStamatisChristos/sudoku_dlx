# Quickstart

## Solve a puzzle
```bash
sudoku-dlx solve --grid "<81chars>" --pretty --stats
```

## Generate
```bash
sudoku-dlx gen --seed 123 --givens 30 --pretty
sudoku-dlx gen --seed 123 --givens 28 --minimal --symmetry rot180
```

## Rate
```bash
sudoku-dlx rate --grid "<81chars>"
```

## Analyze (valid/unique/difficulty)
```bash
sudoku-dlx check --grid "<81chars>" --json
```

## Explain steps
```bash
sudoku-dlx explain --grid "<81chars>" --json --max-steps 200
```

## Batch generate & stats
```bash
sudoku-dlx gen-batch --out puzzles.txt --count 1000 --givens 30 --parallel 8
sudoku-dlx stats-file --in puzzles.txt --limit 5000 --sample 1000 --json stats.json
```

## Trace & visualization
```bash
sudoku-dlx solve --grid "<81chars>" --trace out.json
# Open web/visualizer.html and load out.json
```
