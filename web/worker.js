const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/";
let pyodideReadyPromise = null;

async function loadPyodideOnce() {
  if (pyodideReadyPromise) {
    return pyodideReadyPromise;
  }
  self.postMessage({ type: 'status', message: 'Downloading Pyodide runtime...' });
  importScripts(`${PYODIDE_INDEX_URL}pyodide.js`);
  pyodideReadyPromise = (async () => {
    const py = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
    self.postMessage({ type: 'status', message: 'Initializing solver...' });
    await py.runPythonAsync(`
from typing import List, Tuple

def col_cell(r, c): return r*9 + c

def col_row(r, v):  return 81  + r*9 + (v-1)

def col_col(c, v):  return 162 + c*9 + (v-1)

def col_box(b, v):  return 243 + b*9 + (v-1)

def box_of(r, c):   return (r//3)*3 + (c//3)

ROW_COLS: List[List[int]] = []
ROW_PAYLOAD: List[Tuple[int,int,int]] = []
COL_ROWS_BITS: List[int] = [0]*324
RCV_TO_ROWIDX: dict[Tuple[int,int,int], int] = {}

def _precompute_matrix():
    idx = 0
    for r in range(9):
        for c in range(9):
            b = box_of(r, c)
            for v in range(1,10):
                cols = [col_cell(r,c), col_row(r,v), col_col(c,v), col_box(b,v)]
                ROW_COLS.append(cols)
                ROW_PAYLOAD.append((r,c,v))
                RCV_TO_ROWIDX[(r,c,v)] = idx
                mask = 1 << idx
                for col in cols: COL_ROWS_BITS[col] |= mask
                idx += 1

_precompute_matrix()
ALL_ROWS_MASK = (1 << 729) - 1
ALL_COLS_MASK = (1 << 324) - 1

def iter_set_bits(x:int):
    while x:
        lsb = x & -x
        i = (lsb.bit_length()-1)
        yield i
        x ^= lsb

def is_bit_set(x:int,i:int)->bool: return (x>>i)&1

def clear_bit(x:int,i:int)->int: return x & ~(1<<i)

class BitDLX:
    def _choose_col(self, rows_mask:int, cols_mask:int):
        best_col=None; best_sz=10**9
        for c in range(324):
            if not is_bit_set(cols_mask,c): continue
            cand = COL_ROWS_BITS[c] & rows_mask
            sz = cand.bit_count()
            if sz==0: return c
            if sz<best_sz: best_sz=sz; best_col=c
            if sz<=1: break
        return best_col

    def _cover_row(self, rows_mask:int, cols_mask:int, row_idx:int):
        cols = ROW_COLS[row_idx]
        union_rows=0
        for c in cols: union_rows |= (COL_ROWS_BITS[c] & rows_mask)
        rows_mask2 = rows_mask & ~union_rows
        for c in cols: cols_mask = clear_bit(cols_mask, c)
        return rows_mask2, cols_mask

    def _search(self, rows_mask:int, cols_mask:int, limit:int, keep_one:bool, collect_sol:list, found:list, stack:list):
        if cols_mask==0:
            found[0]+=1
            if keep_one and not collect_sol:
                collect_sol.extend(stack)
            return found[0]>=limit
        c = self._choose_col(rows_mask, cols_mask)
        cand = COL_ROWS_BITS[c] & rows_mask
        if cand==0: return False
        for r in iter_set_bits(cand):
            rows2, cols2 = self._cover_row(rows_mask, cols_mask, r)
            stack.append(r)
            if self._search(rows2, cols2, limit, keep_one, collect_sol, found, stack): return True
            stack.pop()
        return False

    def count_solutions(self, clues:list[tuple[int,int,int]], limit:int=2):
        rows_mask = ALL_ROWS_MASK; cols_mask = ALL_COLS_MASK
        for (r,c,v) in clues:
            row_idx = RCV_TO_ROWIDX.get((r,c,v))
            if row_idx is None or not is_bit_set(rows_mask, row_idx): return 0, None
            rows_mask, cols_mask = self._cover_row(rows_mask, cols_mask, row_idx)
        found=[0]; collect=[]
        self._search(rows_mask, cols_mask, limit, True, collect, found, [])
        if found[0]==0: return 0, None
        grid=[[0]*9 for _ in range(9)]
        for (rr,cc,vv) in clues: grid[rr][cc]=vv
        for rid in collect:
            rr,cc,vv = ROW_PAYLOAD[rid]; grid[rr][cc]=vv
        return found[0], grid

SOLVER = BitDLX()

def parse_linear(vals):
    g=[[0]*9 for _ in range(9)]
    for i,v in enumerate(vals):
        r,c=divmod(i,9); g[r][c]=int(v)
    return g

def clues_from_grid(g):
    return [(r,c,g[r][c]) for r in range(9) for c in range(9) if g[r][c]!=0]
    `);
    self.postMessage({ type: 'status', message: 'Pyodide ready. Enter digits and press Solve.' });
    return py;
  })();
  try {
    return await pyodideReadyPromise;
  } catch (err) {
    pyodideReadyPromise = null;
    throw err;
  }
}

self.onmessage = async (event) => {
  const { type } = event.data || {};
  if (type === 'init') {
    try {
      await loadPyodideOnce();
    } catch (err) {
      self.postMessage({ type: 'error', message: 'Failed to initialize Pyodide.', detail: `${err}` });
    }
    return;
  }
  if (type === 'solve') {
    const { values } = event.data;
    const started = performance.now();
    let py;
    try {
      py = await loadPyodideOnce();
    } catch (err) {
      self.postMessage({ type: 'error', message: 'Pyodide is not available.', detail: `${err}` });
      return;
    }
    try {
      py.globals.set('vals', values);
      const out = py.runPython(`
g = parse_linear(vals)
cnt, sol = SOLVER.count_solutions(clues_from_grid(g), limit=2)
cnt, sol
`);
      const cnt = out.get(0);
      const sol = out.get(1);
      let flat = null;
      if (typeof cnt === 'number' && cnt > 0 && sol !== undefined && sol !== null) {
        const js = sol.toJs({ create_proxies: false });
        flat = [];
        for (let r = 0; r < 9; r++) {
          for (let c = 0; c < 9; c++) {
            flat.push(js[r][c]);
          }
        }
      }
      if (typeof cnt === 'number' && cnt > 0 && Array.isArray(flat)) {
        const elapsed = performance.now() - started;
        self.postMessage({ type: 'result', status: 'ok', solutions: cnt, grid: flat, ms: elapsed });
      } else if (typeof cnt === 'number' && cnt === 0) {
        self.postMessage({ type: 'result', status: 'none' });
      } else {
        self.postMessage({ type: 'error', message: 'Unexpected solver output.' });
      }
      if (sol && typeof sol.destroy === 'function') {
        sol.destroy();
      }
      out.destroy();
    } catch (err) {
      self.postMessage({ type: 'error', message: 'Solver execution failed.', detail: `${err}` });
    }
    return;
  }
};
