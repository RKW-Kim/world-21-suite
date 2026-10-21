# The audit loop

How to improve this codebase without a human in the room. This is the
procedure an autonomous agent should follow, and the one to use when
picking the next thing to work on.

---

## 1. The loop

```
    ┌──────────────────────────────────────────────────────────────┐
    │  1. OBSERVE   read the code, the logs, the running station  │
    │  2. DIAGNOSE  find the cause, with evidence                 │
    │  3. FIX       the smallest change that removes the cause    │
    │  4. VERIFY    tests + the live station + no regressions     │
    │  5. RECORD    commit, PR, and update the docs you touched  │
    └───────────────────────────┬──────────────────────────────────┘
                                │  repeat with the next finding
```

Each pass should be **one idea**. A pass that fixes five things in five
files is five passes that were bundled — and if it regresses, you will not
know which change did it.

## 2. Observe

Sources, in the order that pays off:

1. **The activity log** — `broadcast/activity.db`. The station's own
   account of itself. Look for CRIT rows, for a WARN that repeats, and for
   gaps (a silence where a "Now playing" row should be is a symptom).
2. **The heartbeat** — `broadcast/heartbeat.json`. `pass_ms` is the
   station's pulse; a rising trend is a slow leak (a growing list, an
   unbounded cache, a scan that gets slower with the playlist).
3. **The code**, with the invariants from `AGENTS.md` §3 in hand. Most
   defects in a system like this are invariant violations that a careful
   reader can spot without running anything.
4. **The tests** — they say what the authors believed. A test that
   exercises a path the code no longer takes is a bug in the test.
5. **The dock** — the operator's window onto the station. Anything that
   makes the operator guess is a defect.

## 3. Diagnose

Rules that keep an audit honest:

- **Evidence, not plausibility.** "This could race" is not a finding;
  "these two writers read-modify-write the same file without a lock, and
  the panel's write is unlocked (file:line)" is.
- **Reproduce before fixing** where you can. A one-off script against a
  temp directory beats a theory (this is how the spooler wedge and the
  fail-safe roll were both found).
- **One root cause, one finding.** Six symptoms of the same bug are one
  bug. Fix the cause; the symptoms go with it.
- **Do not report style.** A finding is a defect with a consequence.
- **Rank by consequence**: a bug that ends the show > a bug that makes the
  operator guess > a bug that costs 40 ms.

## 4. Fix

- **Smallest change that removes the cause.** Not the largest one that
  removes it.
- **Match the surrounding code.** The codebase's voice is plain, commented
  where the "why" is not obvious, and it never has a framework.
- **Add the missing log line or alert** while you are there: a defect
  that was invisible is a defect that will come back. (But see the log
  discipline: the station used to log a CRIT every pass, and that noise
  hid the real alerts.)
- **Never take the station lock for granted** on the live files.

## 5. Verify

Three things, all required (see `AGENTS.md` §4):

```bash
# 1. the tests
python3 station/test_spool.py && python3 station/test_fallback.py && \
python3 station/test_playlist_edges.py && python3 station/daemon.py selftest

# 2. the live station
sqlite3 broadcast/activity.db "SELECT ts,level,msg FROM activity_log ORDER BY rowid DESC LIMIT 10;"
cat broadcast/heartbeat.json
python3 station/station_watchdog.py --check

# 3. the operator surface (a screenshot or the dock's own state)
curl -s http://127.0.0.1:8220/api/ping | python3 -m json.tool
```

If the change is in the dock, look at it: load `http://127.0.0.1:8220/dock`
in a browser, exercise the path you changed, and take a screenshot. The
dock is the operator's only window; a change that is correct in the code
and wrong on screen is not verified.

**Do not declare a fix on the strength of a test alone.** The station is a
live system with timing, locks and a renderer in the loop.

## 6. Record

- **Commit**: one idea, a subject that says what changed, a body that
  says why. "Fix the thing" is not a subject; "the spooler no longer
  wedges on a silent item: _current is cleared on the NOAUDIO path" is.
- **PR** (when the repo is remote): what was broken, what you changed, how
  you verified it, and what you did *not* fix. The reviewer has no access
  to your session.
- **Docs**: if you changed an invariant, a format, a knob or a decision,
  the docs changed with it — in the same commit. A repository whose docs
  lie is worse than one with no docs.
- **Known issues**: if you found something you did not fix, write it in
  `docs/KNOWN_ISSUES.md` with a sentence of why. A finding that vanishes
  is a finding that will be re-investigated from scratch.

## 7. Choosing what to work on next

Rank by (consequence × likelihood) ÷ effort, and prefer the classes that
have historically paid:

1. **Silent-corruption bugs** — state that is quietly wrong (a wiped
   cursor, a lost item, a stale flag). They surface as "the station is
   weird" with no other evidence.
2. **The things that end the show** — black frames, a dead plane, a
   queue that cannot advance.
3. **The things that make the operator fight the tool** — ambiguous
   state, actions without confirmation, feedback that lies.
4. **Performance that competes with the render** — the dock runs inside
   OBS; every millisecond it spends is a millisecond the picture does not.
5. **Dead code and stale config** — remove it, or it will mislead the
   next reader (the `monitor` path, the `monitor-av` unit, the stale
   `collection.json`).
6. **Missing observability** — if you cannot see it, you cannot fix it.

## 8. Guardrails for an autonomous pass

- **Do not restart the render plane or the daemon** without a human's
  go. A restart cuts the programme.
- **Do not touch the ad configuration** while testing.
- **Do not commit live state** and do not delete `broadcast/` or `spool/`.
- **Do not enable the publish leg.** Publishing is outward-facing.
- **Keep the working tree clean** between passes: one branch, one idea,
  one commit, one PR.
- **If a fix needs a decision you cannot make** (a policy question, a
  trade-off between two reasonable behaviours), write the question and
  the two options into the PR, pick the safer default, and move on.
- **Stop when the evidence runs out.** A pass that cannot find a
  defensible finding should end with "no findings" — not with a
  speculative refactor.
