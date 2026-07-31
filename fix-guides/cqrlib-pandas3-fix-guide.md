# Fix Guide: cqrlib fails on pandas 3.0 (`datetime64[us]` vs `datetime64[ns]`)

## Problem

Calling `cqrlib.vert_barrier(...)` (and `tri_barrier(...)` with a `t1` argument) raises:

```
ValueError: data index does not contain datetime
```

under the `mlquant` environment (Python 3.12.4, numpy 2.4.6, pandas 3.0.5).

## Root cause

- pandas 3.0 changed the default datetime resolution produced by `read_csv(parse_dates=True)`
  from `datetime64[ns]` to `datetime64[us]` (microseconds).
- `cqrlib` validates datetime inputs with a **strict string equality** check that only
  accepts `"datetime64[ns]"`, so any other resolution (including the new default `[us]`,
  and timezone-aware dtypes) is wrongly rejected.
- The library was originally written for pandas 1.0.3 / numpy 1.17.3 (see notebook comments).

## Files to change

Two files are affected (the datetime dtype checks, plus a follow-on
`DataFrame.append` incompatibility discovered while validating):

```
cqrlib/Labels/triple_barrier_method.py
cqrlib/Util/multiprocess.py
```

### Fix 1 — `tri_barrier`, t1 check (~line 108)

Current code:

```python
elif t1.dtype != "datetime64[ns]":
    raise ValueError("t1 must be pd.Series with datetime, pls use vertical_bar func provided.")
```

Replace with:

```python
elif not pd.api.types.is_datetime64_any_dtype(t1.dtype):
    raise ValueError("t1 must be pd.Series with datetime, pls use vertical_bar func provided.")
```

### Fix 2 — `vert_barrier`, data index check (~line 175)

Current code:

```python
elif data.index.dtype != "datetime64[ns]":
    raise ValueError("data index does not contain datetime")
```

Replace with:

```python
elif not pd.api.types.is_datetime64_any_dtype(data.index.dtype):
    raise ValueError("data index does not contain datetime")
```

### Fix 3 — `vert_barrier`, events check (~line 180)

Current code:

```python
elif events.dtype != "datetime64[ns]":
    raise ValueError("events must be pandas DatetimeIndex")
```

Replace with:

```python
elif not pd.api.types.is_datetime64_any_dtype(events.dtype):
    raise ValueError("events must be pandas DatetimeIndex")
```

## Why `is_datetime64_any_dtype`

- Accepts every datetime64 resolution: `[ns]`, `[us]`, `[ms]`, `[s]`.
- Accepts timezone-aware datetimes (important on pandas 3.x, where naive indexing changed).
- Unlike comparing against the string `"datetime64[ns]"`, it does not depend on numpy's
  dtype string representation.

## Fix 4 — `mp_pandas_obj`, `DataFrame.append` removed in pandas 2.0+

`pandas 2.0` removed `DataFrame.append`, so `tri_barrier` (via `mp_pandas_obj`) fails with:

```
AttributeError: 'DataFrame' object has no attribute 'append'
```

Current code (`cqrlib/Util/multiprocess.py`, end of `mp_pandas_obj`):

```python
    if isinstance(out[0], pd.DataFrame):
        df0 = pd.DataFrame()
    elif isinstance(out[0], pd.Series):
        df0 = pd.Series()
    else:
        return out

    for i in out: df0 = df0.append(i)
    df0 = df0.sort_index(axis=axis) #experimental
    return df0
```

Replace with:

```python
    if not isinstance(out[0], (pd.DataFrame, pd.Series)):
        return out

    df0 = pd.concat(out)
    df0 = df0.sort_index(axis=axis) #experimental
    return df0
```

## Verification notes

The guide's "7408 rows" figure is the per-molecule chunk size (22224 trgt rows / 3 threads),
not the total. With the 24079-bar `dollar_bars.csv` expect: `vb` = 22850, `tb`/`meta_label` = 22207.

## Do NOT change

- `drop_label` and `meta_label` — verified they contain no datetime dtype checks and work
  on pandas 3.0 (meta_label returns numeric `ret`/`bin`, index is plain DatetimeIndex).
- The `dtype`-as-`str` checks such as `isinstance(data.squeeze().dtype, (str, ...))`:
  they are pre-existing defensive checks that happen to pass; leave them alone unless a
  related bug is reported.

## Verification

Run from the AFML workspace with the `mlquant` pyenv:

```bash
cd <repo-root>/AFML
python - <<'EOF'
import numpy as np, pandas as pd
import cqrlib as rs

dollar = pd.read_csv('./sample-data/dollar_bars.csv', sep=',', header=0,
                     parse_dates=True, index_col=['date_time'])
# NOTE: do NOT apply as_unit('ns') here — the goal is that the library
# accepts the native pandas 3.0 'us' index without any workaround.
print('index dtype:', dollar.index.dtype)  # expect datetime64[us]

d_vol = rs.vol(dollar['close'], span0=50)
events = rs.cs_filter(dollar['close'], limit=d_vol.mean())
vb = rs.vert_barrier(data=dollar['close'], events=events, period='days', freq=1)
tb = rs.tri_barrier(data=dollar['close'], events=events, trgt=d_vol,
                    min_req=0.002, num_threads=3, ptSl=[1, 1], t1=vb, side=None)
m_label = rs.meta_label(data=dollar['close'], events=tb, drop=False)
print('vert_barrier rows:', vb.shape[0])
print('tri_barrier  rows:', tb.shape[0])
print('meta_label   rows:', m_label.shape[0])
print('PASS')
EOF
```

Success criteria: the script prints `PASS` with 7408 rows for `vb`/`tb`, and no
`ValueError: data index does not contain datetime`.

## Notes for the agent

- Do not change function signatures or return types.
- Keep the existing error messages unchanged so downstream code/tests stay stable.
- The notebook `AFML 3.1.ipynb` currently contains a workaround
  (`dollar.index = dollar.index.as_unit('ns')`). After this library fix, that line is
  no longer needed and may be removed — but removing it is optional and separate from
  this fix.
