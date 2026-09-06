const PYODIDE_INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/";
let pyodideReadyPromise = null;

function status(message) {
  self.postMessage({ type: "status", message });
}

async function loadRuntimeOnce() {
  if (pyodideReadyPromise) return pyodideReadyPromise;

  pyodideReadyPromise = (async () => {
    status("Downloading Python runtime…");
    importScripts(`${PYODIDE_INDEX_URL}pyodide.js`);
    const py = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });

    status("Loading sudoku_dlx package…");
    await py.loadPackage("micropip");

    const manifestUrl = new URL("./assets/wheel.json", self.location.href);
    const manifestResponse = await fetch(manifestUrl, { cache: "no-store" });
    if (!manifestResponse.ok) {
      throw new Error(`wheel manifest request failed: ${manifestResponse.status}`);
    }
    const manifest = await manifestResponse.json();
    if (!manifest.filename || !manifest.version) {
      throw new Error("wheel manifest is incomplete");
    }

    const wheelUrl = new URL(`./assets/${manifest.filename}`, self.location.href).href;
    py.globals.set("web_wheel_url", wheelUrl);
    await py.runPythonAsync(`
import micropip
await micropip.install(web_wheel_url)
`);
    py.globals.delete("web_wheel_url");

    await py.runPythonAsync(`
from dataclasses import asdict
import json
import sudoku_dlx as sdk


def _web_grid(values):
    vals = [int(v) for v in values]
    if len(vals) != 81:
        raise ValueError("expected 81 cells")
    if any(v < 0 or v > 9 for v in vals):
        raise ValueError("cells must be integers in 0..9")
    return [vals[r * 9:(r + 1) * 9] for r in range(9)]


def _grid_string(grid):
    return sdk.to_string(grid)


def _json(payload):
    return json.dumps(payload, separators=(",", ":"))


def web_solve(values):
    grid = _web_grid(values)
    if not sdk.is_valid(grid):
        return _json({"ok": False, "reason": "invalid"})
    solved = sdk.solve(grid)
    if solved is None:
        return _json({"ok": False, "reason": "unsatisfiable"})
    solutions = sdk.count_solutions(grid, limit=2)
    return _json({
        "ok": True,
        "grid": solved.grid,
        "solution": _grid_string(solved.grid),
        "solutions": solutions,
        "stats": asdict(solved.stats),
    })


def web_analyze(values):
    grid = _web_grid(values)
    analysis = sdk.analyze(grid)
    human = sdk.human_rate(grid)
    analysis["human"] = asdict(human)
    analysis["package_version"] = sdk.__version__
    analysis["machine_version"] = sdk.DIFFICULTY_VERSION
    analysis["human_version"] = sdk.HUMAN_DIFFICULTY_VERSION
    return _json(analysis)


def web_logic(values, max_steps=500):
    grid = _web_grid(values)
    if not sdk.is_valid(grid):
        return _json({"ok": False, "reason": "invalid"})
    result = sdk.logical_solve(grid, max_steps=int(max_steps))
    rating = sdk.human_rate(grid, max_steps=int(max_steps))
    return _json({
        "ok": True,
        "grid": result.grid,
        "steps": result.steps,
        "solved": result.solved,
        "stalled": result.stalled,
        "contradiction": result.contradiction,
        "limit_reached": result.limit_reached,
        "hardest_strategy": result.hardest_strategy,
        "rating": asdict(rating),
    })


def web_generate(seed, difficulty, symmetry):
    parsed_seed = None if seed is None or str(seed).strip() == "" else int(seed)
    symmetry = str(symmetry or "mix")
    difficulty = str(difficulty or "any")
    if difficulty == "any":
        result = sdk.generate_result(
            seed=parsed_seed,
            target_givens=30,
            symmetry=symmetry,
        )
    else:
        result = sdk.generate_rated(
            difficulty,
            seed=parsed_seed,
            symmetry=symmetry,
            max_attempts=64,
        )
    return _json({
        "ok": True,
        "grid": result.grid,
        "solution": result.solution,
        "seed": result.seed,
        "attempts": result.attempts,
        "givens": result.givens,
        "symmetry": result.symmetry,
        "minimality": result.minimality,
        "machine_difficulty": result.machine_difficulty,
        "human_difficulty": asdict(result.human_difficulty),
    })
`);

    const runtimeVersion = py.runPython("sdk.__version__");
    status(`sudoku_dlx v${runtimeVersion} ready in your browser.`);
    return py;
  })();

  try {
    return await pyodideReadyPromise;
  } catch (error) {
    pyodideReadyPromise = null;
    throw error;
  }
}

function parsePythonJson(raw) {
  const text = typeof raw === "string" ? raw : raw.toString();
  if (raw && typeof raw.destroy === "function") raw.destroy();
  return JSON.parse(text);
}

async function callPython(functionName, args) {
  const py = await loadRuntimeOnce();
  const names = [];
  try {
    args.forEach((value, index) => {
      const name = `web_arg_${index}`;
      names.push(name);
      py.globals.set(name, value);
    });
    const expression = `${functionName}(${names.join(",")})`;
    return parsePythonJson(py.runPython(expression));
  } finally {
    names.forEach((name) => py.globals.delete(name));
  }
}

self.onmessage = async (event) => {
  const { type, requestId } = event.data || {};
  if (type === "init") {
    try {
      await loadRuntimeOnce();
      self.postMessage({ type: "ready" });
    } catch (error) {
      self.postMessage({
        type: "error",
        requestId,
        message: "Failed to initialize the browser runtime.",
        detail: String(error),
      });
    }
    return;
  }

  try {
    let payload;
    if (type === "solve") {
      payload = await callPython("web_solve", [event.data.values]);
    } else if (type === "analyze") {
      payload = await callPython("web_analyze", [event.data.values]);
    } else if (type === "logic") {
      payload = await callPython("web_logic", [event.data.values, 500]);
    } else if (type === "generate") {
      payload = await callPython("web_generate", [
        event.data.seed ?? "",
        event.data.difficulty ?? "any",
        event.data.symmetry ?? "mix",
      ]);
    } else {
      return;
    }
    self.postMessage({ type: "result", action: type, requestId, payload });
  } catch (error) {
    self.postMessage({
      type: "error",
      action: type,
      requestId,
      message: "Operation failed.",
      detail: String(error),
    });
  }
};
