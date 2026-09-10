# Related Work & Novelty Positioning

> **Verify before citing.** §§1-6 were located via search; titles/IDs are from result metadata and
> abstracts, not full reads. Pull each PDF, confirm the ID, year and venue, and read at least the
> abstract + limitations section before it goes in the paper. Two or three of these deserve a full read
> (marked ★). §7 (added 2026-09-10) was fetched and read at abstract level for every entry — still
> confirm venue/exact citation details before the paper draft, but the substance has been checked, not
> just surfaced.

---

## 1. The nearest neighbour — read this first

★ **Survival Games: Human-LLM Strategic Showdowns under Severe Resource Scarcity** — arXiv:2505.17937

Closest published work to your project, and you must cite and differentiate from it explicitly.
Setup: 3 agents in a ~6-day survival sim, daily food consumption, starvation = death. LLM agents
(DeepSeek R1/V3, GPT-4o/4o-mini) vs. "humans". Measures deception, stealing, manipulation via a
MACHIAVELLI-derived wrongdoing taxonomy, plus survival duration and a "survival impact score".
Findings: DeepSeek hoards and deceives more; GPT-4o shows restraint; jailbreak prompts sharply raise
violations; an ethics prompt eliminates them.

**Their gap, which is your entire contribution:** *their "humans" are rule-based scripted policies, not
human participants.* Humans follow deterministic rules while LLMs get dynamic prompts — so the two
sides are not playing the same game, and the paper reports **no statistical comparison of behavioural
metrics between human and LLM players.** They compare LLMs to each other.

Your differentiator, stated in one sentence for the intro: *we run real human participants and LLM
agents through an identical action space, identical observation function, identical message channel and
identical log schema on matched random seeds, and report effect-sized statistical comparison plus a
distinguishability classifier.* That is a matched-protocol design, and nobody in this list has one.

---

## 2. LLM societies under commons pressure

★ **Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents (GovSim)** —
Piatti et al., NeurIPS 2024, arXiv:2404.16698 · [code](https://github.com/giorgiopiatti/GovSim)

The canonical LLM commons paper and your closest methodological ancestor. Common-pool resource sim
across fishery / pasture / pollution. Highest survival rate below 54%; only a small fraction of models
sustain the resource. Communication is critical to cooperation; agents fail because they can't reason
about long-run consequences; "universalization" moral prompting substantially improves sustainability.
**No human baseline.** Steal their metric vocabulary (survival time, efficiency, equality, over-usage)
so your numbers are comparable to theirs — that's free credibility, and it lets you write "GovSim
reports X for LLMs; we report the human value of the same metric for the first time."

**Reputation as a Solution to Cooperation Collapse in LLM-based MASs** — arXiv:2505.05029.
Relevant if you add reputation carry-over to the `repeated_trust` scenario.

**Bosses, Kings, and the Commons: Cooperation Under Power Asymmetry in LLM Societies** — arXiv:2605.29062.
Directly relevant to your `asymmetric` scenario — check whether they've already claimed that angle.

**SRAP-Agent: Simulating and Optimizing Scarce Resource Allocation Policy with LLM-based Agent** — arXiv:2410.14152.

---

## 3. LLM vs. human in behavioural games (the comparison literature)

★ **Playing repeated games with large language models** — Akata et al., *Nature Human Behaviour* 2025.
The methodological benchmark for this genre. LLMs do well on self-interested games (iterated PD family),
poorly on coordination games (Battle of the Sexes). High-visibility venue — cite it as the standard your
statistical comparison is trying to meet.

**LLM Agents Do Not Replicate Human Market Traders: Evidence From Experimental Finance** — arXiv:2502.15800.
A strong "divergence" result in a neighbouring domain. Useful if your finding is *divergence*.

**Reasoning Language Models Become Free-Riders in Public Goods Games** — arXiv:2506.23276.
Humans use social learning and norm enforcement; standard LLMs cooperate rigidly by rule; *reasoning*
models show declining/inconsistent cooperation. Direct support for adding a reasoning-vs-standard model
contrast to your model sweep (Phase G) — potentially a headline result on its own.

**Divergent Minds, Convergent Baselines: A Bounded-Rationality Account of LLM-Human Strategic Behaviour**
— arXiv:2605.26437. Reports that across ~15 studies, LLMs are consistently *more* fair/cooperative/
Nash-converging than humans. Sets the prior your results will be read against; if you find the same
direction, you're confirming, and you need scarcity-severity or spatiality to be your novel axis.

**Simulating Cooperative Prosocial Behavior with Multi-Agent LLMs** — IUI 2025, ACM DL 10.1145/3708359.3712149.
LLM agents reproduce the *direction* of human effects but not the *magnitude* — a precise, quotable
framing for your discussion.

**Bias-Adjusted LLM Agents for Human-Like Decision-Making via Behavioral Economics** — arXiv:2508.18600.
Relevant to novelty idea N7 (can prompting close the human gap?).

**Large Language Models as Simulated Economic Agents ("Homo Silicus")** — Horton, arXiv:2301.07543.
The origin citation for "use LLMs as experimental subjects." Cite in the intro framing.

---

## 4. MARL environments and social dilemmas

**Melting Pot** — Leibo et al., arXiv:2107.06857 · [code](https://github.com/google-deepmind/meltingpot).
50+ substrates, 256+ scenarios, designed for cooperation/competition/deception/trust/reciprocity.
Your env is a deliberately minimal cousin — say so, and justify the minimalism: *the environment must
be simple enough for an untrained human to play competently in 15 minutes.* Melting Pot's substrates
are not. That's a real, defensible design argument, not a concession.

**SocialJax** — arXiv:2503.14576. JAX reimplementation, ≥50× faster than Melting Pot RLlib baselines.
Worth a look if RL training time becomes a bottleneck in Phase D.

**Can LLM-Augmented autonomous agents cooperate? An evaluation through Melting Pot** — arXiv:2403.11381.
Prior art for putting LLM agents in a MARL social-dilemma benchmark.

**Coopetition-Gym** — arXiv:2605.02063. Mixed-motive MARL platform; check for env-design overlap.

---

## 5. Generative agent societies, norms, deception

**Generative Agents: Interactive Simulacra of Human Behavior** — Park et al., arXiv:2304.03442.
Obligatory citation; the memory/reflection architecture your LLM layer is a stripped-down version of.

**Emergence of Social Norms in Generative Agent Societies** — IJCAI 2024.

**AgentSociety** — arXiv:2502.08691. Large-scale (10k agents) LLM social simulation. Cite as the
scale end of the spectrum; you're the *validated* end. Scale without a human baseline is exactly the
weakness your paper exploits.

**Static Sandboxes Are Inadequate: ... Open-Ended Co-Evolution in LLM-Based Multi-Agent Simulations** —
arXiv:2510.13982. Useful for your limitations section.

**PAVE: A Cognitive Architecture for Legitimate Violation in Generative Agent Societies** — arXiv:2605.19351.
**Emergent Social Intelligence Risks in Generative Multi-Agent Systems** — arXiv:2603.27771.
Both relevant to the AI-safety framing in Future Work.

---

## 6. Distinguishability / detection

**Large language models pass a standard three-party Turing test** — Jones & Bergen, PNAS.
GPT-4.5 judged human 73% of the time with a persona prompt. Cite to frame your classifier as a
**behavioural** Turing test: not "does it *talk* like a human" but "does it *act* like one under
scarcity." That reframing is the cleanest one-line pitch your paper has.

**What Does It Take to Detect an AI Agent? Minimal Feature Sets for Behavioral Detection** — arXiv:2607.26935.
Three-class human/bot/agent detection; argues binary detectors misroute agents. Methodologically close
to your `classifier.py` + SHAP step.

**Understanding LLM Agent Behaviours via Game Theory: Strategy Recognition, Biases and Multi-Agent
Dynamics** — arXiv:2512.07462. Encodes game trajectories as state-action sequences and classifies
against canonical strategies (ALLC, ALLD, TFT, WSLS). **Directly borrowable:** run their strategy
taxonomy over your logs and report the AI vs. human distribution over strategy labels — a strong
secondary results figure for nearly no extra work.

**Validated Hypotheses as a Lens for Human-Likeness Evaluation in AI Agents** — arXiv:2605.15473.

**Deliberate Lab: A Platform for Real-Time Human-AI Social Experiments** — arXiv:2510.13011.
Check this before Group 1 builds Streamlit from scratch — it may do half their job, or at minimum
give them a defensible protocol to cite.

---

## 7. Second literature pass (2026-09-10) — verified, not just found

Everything below was fetched and read (abstract-level), not just surfaced by a title. **No direct
scoop of the core contribution** — nothing combines survival-stakes scarcity + machine-verifiable
deception + a distinguishability curve — but two of these independently validate pieces of the
*methodology*, which changes how precisely the contribution claim (§8) needs to be worded, and one
is directly relevant to the Blocker 1 disclosure decision the team already made.

★ **Cooperate to Compete: Strategic Coordination in Multi-Agent Conquest** — arXiv:2604.25088.
**Read this one.** 82 games, one human + AI opponents; the same starting positions are then
replayed AI-only for direct comparison. That is *exactly* the focal-player-substitution mechanism
proposed for this project (§8, and `agents/PHASE_PLAN.md` Phase B) — same seed/position, swap who
occupies one seat, compare. Independently arrived at, in a completely different domain (territorial
conquest and diplomatic negotiation, not resource scarcity), with no survival stakes and no
deception-verification mechanism. **This is good news, not bad news**: it means the core
methodological move isn't an idiosyncratic hack, it's converged-on-independently as the right way
to run this kind of comparison. Cite it explicitly as the nearest methodological precedent for
focal-player substitution, and be precise in the intro that the *domain* (scarcity/commons,
survival stakes) and the *deception mechanism* (structured, verifiable claims) are what's new here,
not the substitution trick itself.

★ **Collective cooperation without individual fidelity in LLM agents** — arXiv:2606.30454 (June
2026). A genuinely matched protocol: nine open-weight LLMs vs. real human data in a large-scale
networked Prisoner's Dilemma, same interaction protocol, payoff structure, and network topologies
on both sides. No resource scarcity or survival mechanic — purely an abstract networked PD. The
headline finding is the one worth building on: **LLM agents reproduce human-like *macro*-level
cooperation trajectories while their *individual*-level decision rules diverge from humans'
underlying mechanisms** — collective outcomes look human-like even when the behavioral
distributions producing them aren't. That's a direct, usable frame for novelty proposal N3
(distinguishability as a function of scarcity): the hypothesis becomes "the macro/micro
dissociation this paper finds in an abstract PD *widens* under resource scarcity, where individual
survival incentives diverge more sharply from aggregate patterns" — a sharper, better-motivated
version of N3 than the original phrasing, and one line further from something a reviewer could call
obvious.

**Normative Equivalence in Human-AI Cooperation: Behaviour, Not Identity, Drives Cooperation in
Mixed-Agent Groups** — arXiv:2601.20487. Humans play in real mixed human-AI groups, with disclosure
of co-player identity varied. Core finding: *observed partner behavior*, not the disclosed
human/AI label, is what drives subsequent cooperation — disclosure has only "bounded normative
effects." **Directly relevant to the team's Blocker 1 decision.** Group 1 already chose disclosure
(the consent screen tells participants their co-players are computer-controlled) — this paper is
evidence that choice is unlikely to badly distort the results, since identity labels turned out to
matter less than behavior itself in a comparable setting. Worth a sentence in Methodology 4.3
justifying the disclosure choice, and worth citing if novelty proposal N10 (an undisclosed-vs-
disclosed manipulation) ever gets built.

**CoopEval: Benchmarking Cooperation-Sustaining Mechanisms and LLM Agents in Social Dilemmas** —
arXiv:2604.15267. Six LLMs (Claude Sonnet 4.5, GPT-5.2, Gemini 3, GPT-4o, Qwen3-30B) across four
cooperation mechanisms (repetition, reputation, mediation, contracting) and four dilemmas (PD,
Traveler's Dilemma, Trust Game, Public Goods Game). **No human baseline at all** — further evidence
for the gap-in-the-literature table in §8, and a second, more recent benchmark alongside GovSim to
name in the intro as "even the newest LLM-cooperation benchmarks still have no human reference."
Its mechanism taxonomy (repetition/reputation/mediation/contracting) is a clean vocabulary for
describing what `repeated_trust`'s reputation-carryover design is doing, if that scenario needs
tighter framing later.

**LLM Agents as Static Level-k Players in Behavioural Games** — arXiv:2606.27845. Public goods game
and beauty-contest; finds LLMs behave as *static* level-k reasoners (k set by model scale) with no
within-game belief updating or backward induction across rounds. Relevant to interpreting
`repeated_trust`: if this generalizes, LLM agents may not actually adapt their strategy across the
three 10-round blocks the way the scenario is designed to test — worth watching for in the Phase G
trial data, and worth citing either way (confirms or refutes it in a spatial/survival setting).

**Hierarchical Control in Multi-Agent Games: LLM-based Planning and RL Execution** — arXiv:2606.20014.
A different hybrid RL+LLM split than this project's: LLM as a *high-level strategic planner*, RL as
the *low-level tactical executor* it directs — an abstraction-layer hierarchy, not a decision-type
router. This project's Phase D/F design routes by *kind of decision* (RL handles reflexive
movement/gathering, LLM handles social decisions) rather than by *level of abstraction*. Cite as
related hybrid-architecture prior art in Methodology 4.2, and use the contrast to make the
design choice legible: this isn't "we also did a hybrid," it's a specifically motivated division
matched to what Gate D/E's cost and social-reasoning requirements actually needed.

**LLMs as Policy-Agnostic Teammates: A Case Study in Human Proxy Design for Heterogeneous Agent
Teams** — arXiv:2510.06151. Relevant to co-player policy design (`agents/coplayers.py`) if the
fixed cooperator/free_rider/tit_for_tat/random roster ever needs a more principled "how do you
design an agent meant to stand in for a class of teammate" justification.

---

## 8. Where the gap actually is

Three literatures, each missing the other's key ingredient:

| Literature | Has | Missing |
|---|---|---|
| LLM commons societies (GovSim, AgentSociety, CoopEval) | Rich multi-agent scarcity/cooperation dynamics | Any human baseline |
| LLM-vs-human behavioural games (Akata, PGG work) | Rigorous human comparison | Only 2-player, abstract, no survival stakes |
| MARL social dilemmas (Melting Pot) | Spatial, embodied, survival stakes | No LLMs, no humans, no natural-language channel |
| Matched-protocol human/AI studies (arXiv:2604.25088, 2606.30454 — §7) | The exact comparison methodology this project uses | Abstract PD or territorial conquest; no scarcity, no survival stakes, no verifiable deception |

**Your position, precisely stated after §7's second pass:** not "the first matched-protocol
comparison" — two concurrent papers now share that methodology in other domains (§7). The actual
claim is narrower and stronger for it: **the first matched-protocol human–AI comparison under
*survival-stakes resource scarcity*, with a *machine-verifiable* deception channel, showing
AI-vs-human distinguishability is itself a measurable, scarcity-dependent quantity.** Every clause
in that sentence is load-bearing — drop any one and a existing paper already covers it. Word the
intro's contribution paragraph this precisely; a looser "first matched-protocol study" claim is now
falsifiable by a citation search a reviewer will actually run.

> ⚠️ **The "spatial, embodied" half of that claim is not currently true.** `move` is a no-op in the
> human app and no grid is rendered — see Blocker 3 in `INTEGRATION_ISSUES.md`. Either the grid gets
> implemented on both sides, or drop spatiality from the claim. Do not let this one drift: it is
> precisely the kind of overstated methods sentence a reviewer checks against the released code.
> Spatiality is our *weakest* novelty claim and the most expensive to build. The matched protocol is
> the strong one and it costs nothing extra.

### The design that carries the novelty: focal-player substitution

Forced by the merge (the human app has no co-players), and it turns out to be a better design than two
independently-run societies:

> Every session has five players. Four are co-players on a fixed policy, supplied by the agents track.
> The fifth — the *focal* player — is a human in one arm and an AI agent in the other. Same seed means
> the co-players behave identically across arms. Only the focal player changes.

Write this up as a deliberate methodological choice in §4.3, not as a limitation. Two independently-run
societies would differ in a dozen uncontrolled ways; here the causal comparison is clean, and it's
standard practice in experimental economics (programmed co-players / confederates). It is also the
sharpest possible contrast with arXiv:2505.17937, whose weakness was that its *humans* were scripted:
in our design the co-players are scripted **and disclosed**, and the focal player is genuinely a person
on one side and genuinely an agent on the other.

**Resolved:** the disclosure question was on the critical path when this was first written; Group 1's
"Add human communication action and disclosure" commit settled it — participants are told their
co-players are computer-controlled, in both the consent screen and the instructions screen. The LLM
prompt (`agents/llm_reasoning.py`'s `CO_PLAYER_DISCLOSURE`) says the same thing, copied to match. See
INTEGRATION_ISSUES.md Blocker 1 for the reconciliation and §7's note on arXiv:2601.20487, which found
that disclosed co-player identity has only "bounded normative effects" on cooperation — reassuring
evidence that this choice is unlikely to badly distort the comparison.

**One-sentence contribution claim (revised per §7):**
> We contribute the first matched-protocol human–AI behavioural comparison under *survival-stakes*
> resource scarcity, with a *machine-verifiable* deception channel, and show that AI-vs-human
> distinguishability is itself a measurable, scarcity-dependent quantity.

---

## 9. Novelty proposals, ranked by (impact ÷ effort)

### Tier 1 — do these; they're cheap and they make the paper

**N1. Scarcity dose–response curve.** Don't run one drought — sweep severity ∈ {0, 0.3, 0.5, 0.7, 0.9}
and plot each metric against it. Compare the *slopes* (cooperation elasticity, dShare/dSeverity), not
just the means. A single drought gives you "AI shares less than humans (p<0.05)" — a slope gives you
"**human cooperation collapses non-linearly past 70% scarcity while LLM cooperation degrades linearly**,"
which is a finding with a shape. Almost free: it's a loop variable in Phase G.

**N2. Machine-verifiable deception via slotted messages.** (Phase C.) Structured claim slots make
`deception_rate` and `promise_break_rate` arithmetic, not judgement. Every related paper here either
hand-codes deception or uses an LLM judge, and both are attackable in review. Yours isn't. Say so
explicitly in Methodology — it's a methodological contribution, not just an implementation detail.

**N3. Distinguishability as a dependent variable.** The roadmap treats classifier accuracy as one final
number. Make it a *curve*: fit the classifier separately per scarcity level and report AUC vs. severity.
The claim "**AI and human behaviour are nearly indistinguishable under abundance and diverge sharply
under scarcity**" is a far better abstract sentence than "our classifier reaches 82% accuracy." Same
data, same code, one extra loop.

**Sharper framing after §7:** arXiv:2606.30454 finds that in an abstract networked Prisoner's Dilemma,
LLM agents reproduce human-*like macro* cooperation trajectories while their *individual*-level
decision rules diverge from humans' underlying mechanisms — aggregate behaviour looks human, the
mechanism producing it doesn't. Frame N3's prediction explicitly against that: this study's hypothesis
is that the macro/micro dissociation they found in the abstract case *widens measurably as scarcity
increases* — individual survival incentives should pull decision rules further from human patterns
even where aggregate metrics (mean hoarding rate, mean survival) still look similar. That's a directly
falsifiable, citable extension rather than a standalone claim invented from nothing.

**N4. Cross-model generalisation of the AI signature.** Train the classifier on model A's trials, test on
models B and C. If it transfers, there's a *universal* behavioural AI signature — a genuinely strong
claim with AI-safety and auditing implications. If it doesn't, "AI behaviour" is model-specific, which
is an important negative result and a direct challenge to every paper that generalises from one model.
You cannot lose this experiment. Cost: one extra model in the Phase G sweep.

**N5. Reasoning vs. non-reasoning models.** arXiv:2506.23276 finds reasoning models free-ride more in
public goods games. Include one reasoning and one standard model in the sweep and test whether the
effect replicates under spatial scarcity. Cheap replication, high citation value.

### Tier 2 — strong, if time allows

**N6. Reflex/deliberation rate as a reported finding.** You're logging `decision_source` anyway (Phase F).
Report *how often* the agent deliberates and how that rate moves with scarcity, then compare it to
human response latency (Group 1 should log time-per-decision — tell them now, it's one field). An
"AI deliberation rate vs. human deliberation time" figure is novel and costs you nothing but a log field.

**N7. Persona-prompt lever — can prompting close the gap?** Run the primary arm under three system
prompts: neutral, "maximise your own survival", and "behave as a typical human participant would."
Measure distinguishability AUC under each. If prompting collapses the gap, that's an alignment and an
AI-safety result (behaviour is a *promptable surface*, not a fixed property). If it doesn't, the
divergence is architectural — a deeper and more interesting claim. Directly extends
arXiv:2508.18600 and the Survival Games prompt-sensitivity finding.

**N8. Human-judge baseline vs. classifier.** Show anonymised trial transcripts to a handful of humans
and ask them to label AI or human. Compare human-judge accuracy to your classifier's AUC. If the
classifier beats human judges, the behavioural signature is *real but not perceptible* — the single
most quotable result available to you, and it costs one extra Streamlit screen at the debrief stage
(Group 1 can bolt it on; there's no extra recruitment and probably no ethics amendment).

**N9. Strategy-taxonomy overlay.** Apply the ALLC/ALLD/TFT/WSLS classification from arXiv:2512.07462
to your trajectories and report the AI vs. human distribution over strategy archetypes. Reuses existing
published methodology; adds an interpretable results figure.

### Tier 3 — only if you're ahead of schedule

**N10. Mixed human–AI groups.** ~~Only if ahead of schedule~~ — **this is now the baseline design, not
an extension.** Focal-player substitution (§7) means every human session already *is* a mixed human–AI
group. What remains optional is the manipulation: vary whether participants are told the co-players are
computer-controlled, and measure whether human cooperation shifts on belief alone. That variant is a
strong CHI-track angle and needs the ethics submission to cover both disclosure conditions — so decide
by **Week 3** or not at all.

**N11. Release `ScarcityBench`.** Package env + AI logs + the human reference distribution as an open
benchmark. The human data is the genuinely scarce asset here — nobody else has it, and a benchmark
with a human reference distribution attracts citations long after the paper. Cost is mostly packaging
and a licence/ethics check on releasing anonymised human logs — clear that with your ethics submission
in Week 3 (adding a data-release clause later is painful).

**N12. Pre-register the hypotheses.** Post predictions to OSF before running trials. Costs an afternoon,
and it converts "we found p<0.05 across 12 metrics" into a confirmatory result. Reviewers at
AI-for-social-good and HCI venues notice this.

### Explicitly *not* recommended

- More scenarios. Four is already ambitious for a 12-week project with human recruitment.
- Larger grids / more agents. Adds compute and human confusion, adds no claim.
- Fine-tuning an LLM. Enormous cost, no contribution to the research question.
- LLM-as-judge for deception. N2 makes it unnecessary and it's the weakest part of comparable papers.

---

## 10. Venue implications

- N1 + N3 + N4 → **AI-for-social-good / AI-safety workshop** at NeurIPS/ICML/AAAI. The auditing angle
  ("can we detect AI agents from behaviour alone?") is what these venues want.
- N8 + N10 → **CHI/HCI workshop**. Human perception of AI co-players.
- N11 → makes the arXiv preprint durably citable regardless of venue outcome.

Post to arXiv either way, as the roadmap says. Given that Survival Games (2505.17937) is this close to
your framing, **priority matters** — get the preprint up as soon as results are stable.
