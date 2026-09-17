# Integration Issues — both branches, raised from `group2-agents`

Written after reading Group 1's merged work (`human_interface/app.py`,
`logging_utils.py`, `session_analysis.py`, root `LOGGING_SCHEMA.md`).

**None of this is a criticism of the code** — the Streamlit flow is clean, the schema doc is good, and
the debrief screen is further along than the roadmap asked for. These are *cross-branch* mismatches that
only show up when you put the two halves side by side, and they are far cheaper to fix now than after
human recruitment starts.

**Read the three blockers before the next team meeting.** Each one currently makes a metric in Phase 3
of the roadmap impossible to compute.

---

## 🔴 Blocker 1 — The human plays alone; there are no other players

`app.py` has `NUM_AGENTS_ON_ISLAND = 5`, and the instructions tell the participant they are one of five
players on an island. But no other players exist anywhere in the code. `share` subtracts 1 from the
participant's own water (`app.py:152-153`) and that unit goes nowhere. Nobody gathers, nobody shares
back, nobody depletes the pool.

Right now the human is playing solitaire against a fixed resource curve.

**What this costs us.** Of the six metrics in the roadmap's Phase 3 Step 1:

| Metric | Computable from human logs today? |
|---|---|
| Hoarding index | Partly — but see Blocker 3 |
| Sharing rate | Degenerate — sharing has no recipient |
| Deception rate | **No** — requires claims about state to other players |
| Alliance formation rate | **No** — requires repeated pairs |
| Survival rate | Yes |
| Gini coefficient | **No** — requires a distribution across agents |

The paper's central comparison is between an AI *society* and a human *society*. We cannot compare a
5-agent AI society against a 1-human solitaire game.

### Recommended fix: focal-player substitution

Don't try to get five humans into a session simultaneously — scheduling that with 25–30 participants
will sink the timeline. Instead:

> Every session has 5 players. Four are **co-players** driven by a fixed policy that Group 2 supplies.
> The fifth is the **focal player** — a human in the human arm, an AI agent in the AI arm. Same seed
> means the co-players behave identically across both arms. We compare only the focal player.

Why this is better than what either of us originally planned:

- **It is a strictly matched comparison.** The only thing that changes between arms is the focal player.
  Two independently-run societies would differ in a dozen uncontrolled ways.
- It makes every metric above computable again.
- It's standard practice in experimental economics (confederates / programmed co-players), so it's
  defensible in review rather than a compromise.
- It removes the multi-participant scheduling problem entirely.
- It sharpens our differentiation from the nearest published work (arXiv:2505.17937), whose weakness was
  that its *humans* were scripted. Here the co-players are scripted and disclosed; the focal player is
  real on one side and an agent on the other.

**Group 2 owes Group 1** a co-player policy module with a frozen interface, early — see Phase B in
`agents/PHASE_PLAN.md`. Group 1 shouldn't have to write agent behaviour.

**Ethics decision needed, and it's on the critical path.** The current consent text says water is
"shared with a few other players," which implies humans. Two options:

1. **Disclose** — tell participants the other players are computer-controlled. No deception, no
   amendment needed, but known-bot co-players may change how people cooperate.
2. **Withhold until debrief** — standard mild deception, needs it written into the ethics submission.

Whichever we choose, **the LLM agent must be told exactly the same thing in its prompt.** If humans
believe they're playing people and the LLM is told it's playing bots, the comparison is dead. Decide
this with the guide before the ethics form is submitted.

---

## 🔴 Blocker 2 — `communicate` is missing from the human action space

`app.py:27` — `ACTIONS = ["gather", "share", "hoard", "move", "skip"]`.

But `LOGGING_SCHEMA.md:31` lists `communicate` as a valid `action_type`, and the instructions screen
(`app.py:99-100`) tells participants "You may also send a short message to another player when you
share or communicate." The action is documented and promised to participants but not implemented.

Today a message can only be attached to a `share` (`app.py:142`), so a participant can never make a
standalone statement — which means they can never make a *claim* about their own state, which means
**deception cannot occur, let alone be measured.** Deception is one of the three behaviours named in
our own problem statement in `MSE-1(TODO)`.

**Fix:** add `communicate` as a sixth action with a target and a message. Group 2's environment will
expose the identical action.

### Bundled ask: make messages structured, not free text

This is the change with the highest payoff-to-effort ratio in the whole project, and it has to land
before recruitment.

Instead of one free-text box, a message carries a slot:

```python
{
  "kind":    "claim_stock" | "promise_share" | "request" | "accuse" | "none",
  "value":   int | None,      # claimed stock, or promised amount
  "target":  "A2" | "all",
  "surface": "I only have 1 left, please spare some"   # optional free text, for the qualitative pass
}
```

In the UI this is one dropdown plus a number input plus the existing text box — maybe fifteen lines.

What it buys: **deception becomes arithmetic.** `claim_stock.value != true_stock` is a lie, provably,
with no interpretation. Promise-breaking is `promised at round t, didn't execute at t+1`. Every
comparable paper either hand-codes deception or asks an LLM to judge it, and both get challenged in
review. Ours can't be.

The free-text `surface` field is kept, so the qualitative transcript excerpts in the roadmap's Phase 3
Step 4 still work.

---

## 🔴 Blocker 3 — `move` and `hoard` do nothing; there is no grid

In `app.py:155-158`, `move`, `hoard` and `skip` all fall through with `pass`. There is no grid rendered
anywhere — `GRID_SIZE = 5` is declared and never used.

Two separate consequences:

**`hoard` and `skip` are mechanically identical.** Choosing between them is pure self-labelling, not
behaviour. The hoarding index would be measuring what participants *say* they're doing, not what they
do. Either give hoard a real effect (e.g. it protects your stock from a shared-pool draw, or it's the
only action that carries stock over without decay) or drop it and derive hoarding from gather-vs-share
ratios instead.

**No spatial component.** This one has a knock-on effect for the paper. Our differentiation from the
LLM-vs-human behavioural games literature (Akata et al. and similar) rests partly on our game being
*spatial and embodied* where theirs are abstract 2×2 matrix games. If `move` is a no-op, that claim
isn't true and a reviewer will find it.

**Decision required — pick one, don't drift:**

- **(a) Implement the grid.** Agents occupy cells, resources are per-cell and regenerate locally, `move`
  changes what you can reach and who can see you. Keeps the spatiality claim; costs Group 1 a grid
  render and Group 2 real per-cell dynamics.
- **(b) Drop spatiality honestly.** Remove `move` and `GRID_SIZE`, describe the study as a repeated
  multi-player commons game, and lean the novelty on the matched protocol and the verifiable-deception
  channel instead. Cheaper and still publishable — see `paper/RELATED_WORK.md`.

Group 2's recommendation is **(b) if we're at all tight on time.** Spatiality is the weakest of our
novelty claims and the most expensive to build; the matched protocol is the strong one and it costs
nothing extra. But it must be a decision, not something we discover in Week 9.

---

## 🟠 Important — fix before any real trials run

### 4. Two schema files, and the populated one isn't where the code says it is

- `LOGGING_SCHEMA.md` (repo root) — populated, good content.
- `data/LOGGING_SCHEMA.md` — 0 bytes, and it's the path referenced by `logging_utils.py:6`,
  `CLAUDE.md`, and the roadmap's repo structure.

**Fix:** keep one. Group 2 proposes the root file is canonical (it's already written and already
merged); delete `data/LOGGING_SCHEMA.md` and fix the docstring reference. Either way, one file.

### 5. Game constants are duplicated across branches with a comment asking us to be careful

`app.py:21` says `# CONFIG (keep in sync with agents/environment.py in Group 2)`. That comment is a
promise that will be broken — probably within two weeks, silently, and we'd find out during analysis.

**Fix:** one `common/config.py`, imported by both sides. Group 2 will write it in Phase A.

**Group 1's shipped numbers become canonical** — they're closer to a real participant session than the
values Group 2 had planned, and Group 1's code already ships. Group 2 will conform:

| Constant | Group 1 shipped | Group 2 had planned | Canonical |
|---|---|---|---|
| Grid | 5×5 | 5×5 | 5×5 (pending Blocker 3) |
| Players | 5 incl. participant | 4 | **5** |
| Rounds | 10 | 12 | **10** |
| Drought round | 6 | 6 | **6** |
| Starting water | 5 | — | **5** |
| Survival cost / round | 2 | 1 | **2** |
| Gather yield | 3 normal / 1 drought | — | **3 / 1** |
| Death condition | `resource >= 0` is alive | stock 0 = dead | **`>= 0` alive** |

Note the death rule: at exactly 0 water the participant is alive. Group 2's environment will match this,
but flag it — an agent sitting on 0 can still act, which is worth being deliberate about rather than
inheriting by accident.

### 6. The schema can't record what our analysis needs

Nothing in the current schema identifies *which experimental condition* a row came from. We can't
compute anything conditioned on scarcity level, we can't match an AI trial to its human counterpart,
and we can't tell which arm produced a row.

**Fix:** add a nested `meta` object rather than new top-level fields, so we never have to renegotiate
the top level again:

```json
"meta": {
  "severity": 0.7,            // scarcity level, for the dose-response sweep
  "seed": 42,                 // matched between the human and AI arm
  "arm": "hybrid",            // rl_only | llm_only | hybrid | human
  "model": "…",               // null for human rows
  "decision_latency_ms": 4210,// how long the decision took — humans and AI both
  "claim": { … }              // the structured message slot from Blocker 2
}
```

`decision_latency_ms` is the one to add even if we add nothing else: it's a single Streamlit timer, and
it's the human-side counterpart to Group 2's LLM deliberation logging. Once recruitment starts it is
unrecoverable.

### 7. Nothing validates a log row

`logging_utils.log_action()` builds a dict and writes it (`logging_utils.py:39-56`). If a field name,
type or enum value drifts on either side, nothing catches it until analysis in Week 8.

**Fix:** Group 2 ships `common/schema.py` with `validate_row()` in Phase A. Group 1 calls it inside
`log_action()` before the write. One import, one line.

---

## 🟡 Minor — worth fixing when you're next in the file

8. **Timestamp format.** `logging_utils.py:51` writes timezone-aware ISO (`…+00:00`); the schema example
   shows a naive timestamp. Harmless as long as the validator accepts both — just pick one and say so.

9. **Dead comparison.** `app.py:140` filters share targets with `if f"A{i}" != st.session_state.participant_id`,
   but `participant_id` is `P####` format, so the filter never excludes anything. Harmless today,
   confusing later.

10. **Scenario enum.** `LOGGING_SCHEMA.md:30` allows `calm`, `drought`, `repeated_trust`.
    `agents/PHASE_PLAN.md` proposes a fourth, `asymmetric` (unequal starting stock — the condition where
    human fairness norms diverge most from LLM behaviour). Either add it to the enum or Group 2 drops it.

11. **`SCENARIO` is hardcoded to `"drought"`** (`app.py:26`), so the human app can only ever run one of
    the three scenarios. Needs to become a session parameter before the human trials in Week 6.

---

## 📅 One scheduling item: `MSE-1(TODO)` isn't in either group's plan

The MSE-1 deliverable needs, among other things, **EDA on real data (2 marks)** and a **literature
survey (5 marks)**.

- The literature survey is largely covered by `paper/RELATED_WORK.md`, already on `group2-agents` —
  three areas with citations and an explicit statement of what each is missing, which is what the
  rubric asks for. Reuse it.
- The EDA needs *actual numbers*. `MSE-1(TODO)` says it explicitly: pilot data beats hypothetical data
  for marks.

**Implication for Group 2:** we need a handful of AI pilot trials out of Phase B early — even with
random or trivially simple agents — purely to have real distributions to plot. That's now an explicit
milestone in `agents/PHASE_PLAN.md` rather than a side effect of Phase G.

---

## Suggested agenda for the next team meeting

1. Blocker 1 — agree focal-player substitution, and **make the ethics call on disclosure**. (Critical
   path; blocks the ethics form.)
2. Blocker 2 — agree `communicate` + structured message slots. (Blocks recruitment.)
3. Blocker 3 — grid or no grid. (Blocks the paper's framing.)
4. Items 4–7 — schema consolidation, shared config, `meta` block, validation. (Group 2 will do the work;
   just needs sign-off.)
5. Confirm who owns the MSE-1 sections and by when.
