# Fix Guide: `cs_filter` threshold units + broken UserWarning

## Problem

Calling `cs_filter(data, limit=d_vol.mean())` (as done in AFML 3.1.ipynb) floods
events: 22,890 out of 24,079 bars become events (~95%), instead of a sparse set
of meaningful CUSUM events.

## Root cause (experimentally confirmed)

- `cs_filter` compares `limit` against **price-point diffs** (`data.diff()`).
- `d_vol.mean()` ≈ 0.0055 is a **return** (0.55%), not a price move.
- Relative to a ~2000-point price series (median |bar diff| = 1.5 pts), 0.0055
  points is ~0.0003% — so the cumulative sum crosses the threshold on nearly
  every bar.

Evidence from `AFML/scripts/compare_log_vs_abs.py` (same CUSUM logic):

| variant | threshold | events | trigger move % |
|---|---|---|---|
| abs, notebook limit (return units) | 0.0055 pts | 22,890 | 0.10 ± 0.10 |
| abs, fair limit (price units) | 11.38 pts (= vol × mean px) | 1,485 | 0.66 ± 0.13 |
| log, fair limit (log-return units) | ln(1.0055) | 1,533 | 0.65 ± 0.12 |

Conclusion: the CUSUM core is correct. The mismatch is purely the **units of the
threshold** — with unit-consistent thresholds, absolute vs log prices produce
nearly identical event sets. Do NOT change the diff transform (docstring forbids
log; not needed).

## File to change

```
cqrlib/Filters/filters.py   (function cs_filter)
```

### Fix 1 — broken warnings (bug, lines ~42 and ~44)

Current code constructs a `UserWarning` object that is never issued:

```python
if isinstance(limit, (list, np.ndarray, pd.Series)):
    limit = float(limit.mean())
    UserWarning('Func does not accept numpy array, convert limit to mean value as estimate')
elif isinstance(limit, (int, float)):
    limit = float(limit)
    UserWarning('Convert limit to float value as estimate')
```

Replace both `UserWarning('...')` calls with `warnings.warn('...')`, and add
`import warnings` at the top of the file.

### Fix 2 — units guard (new, after limit is a float)

Add a warning that fires when `limit` is tiny relative to typical bar-to-bar
price moves (the flooding condition). Calibrated on this dataset:

- median |diff| = 1.5 points
- return-unit limit 0.0055 → 0.37% of median |diff|  (should warn)
- fair limit 11.38 → 759% of median |diff|  (should not warn)

Suggested code:

```python
import warnings  # top of file

# after limit has been coerced to float:
diff_scale = data.diff().abs().median()
if limit < diff_scale * 0.01:
    warnings.warn(
        "limit is ~100x smaller than the typical bar-to-bar price move; it looks "
        "like a RETURN (e.g. d_vol.mean()). cs_filter compares against price-point "
        "diffs, so pass a price-scaled threshold, e.g. d_vol.mean() * data.mean()."
    )
```

Notes for the agent:
- `diff_scale` must be computed on the original data (before any limit coercion).
- The 0.01 multiple is calibrated to this dataset; if the guard proves noisy on
  other assets (e.g. low-priced instruments), relax to 0.001. The principle is:
  warn only when the threshold is far below the typical bar move (i.e. when the
  filter degenerates to "every bar is an event").
- This is a warning, not a behaviour change — callers keep full control.

### Fix 3 — docstring clarification

The docstring already says "use original price series to derive standard
deviation as an estimate"; make it explicit:

```
limit must be in the same units as the price diffs (points). If you have a
return-based estimate (e.g. d_vol), scale it by the price level first:
    cs_filter(data, limit=d_vol.mean() * data.mean())
```

## Do NOT change

- The CUSUM loop itself (`_up`/`_dn` accumulation) — verified correct.
- The `data.diff()` transform — the experiment shows abs and log give equivalent
  events with unit-consistent thresholds, so switching to log is not needed and
  is explicitly forbidden by the docstring.

## Verification

Run from the AFML workspace with the `mlquant` pyenv:

```bash
cd <repo-root>/AFML
python scripts/compare_log_vs_abs.py
```

Expected after the fix:
1. The "abs events, notebook limit (returns)" variant triggers the new units
   warning (and the Fix-1 warning now actually appears in stderr).
2. Counts stay 1,485 / 22,890 / 1,533 (warning only — no behaviour change).
3. Sanity check of the intended usage:

```bash
python - <<'EOF'
import pandas as pd
import cqrlib as rs
dollar = pd.read_csv('./sample-data/dollar_bars.csv', sep=',', header=0,
                     parse_dates=True, index_col=['date_time'])
dollar.index = dollar.index.as_unit('ns')
d_vol = rs.vol(dollar['close'], span0=50)
ev = rs.cs_filter(dollar['close'], limit=d_vol.mean() * dollar['close'].mean())
print(len(ev))  # expect ~1485, no units warning
EOF
```

## Follow-up (outside cqrlib)

The notebook `AFML 3.1.ipynb` currently calls
`cs_filter(dollar['close'], limit=d_vol.mean())`. After this fix it will emit the
units warning; update the call to
`cs_filter(dollar['close'], limit=d_vol.mean() * dollar['close'].mean())`
so events become meaningful (~1,485 instead of ~22,890). This is a separate
change from the cqrlib fix.
