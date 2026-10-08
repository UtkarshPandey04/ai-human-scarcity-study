# Literature Review: Human vs. LLM-Agent Behaviour under Resource Scarcity

Generated: 2026-10-06
Review type: **Scoping review** (single reviewer; not systematic, so do not describe it as one in the paper)
Search window: 2023-01-01 to 2026-10-06
Databases: arXiv API, Semantic Scholar Graph API, OpenAlex (used as the route into ACM/IEEE/Springer/OUP venues), plus forward citation chasing on Semantic Scholar
Companion files: `paper/lit_review_data/` (search and dedup scripts, search log, per-record screening decisions in `screening.csv`)

This file **verifies** `RELATED_WORK.md` and **extends** it. RELATED_WORK.md is unchanged; corrections are listed in §5 for whoever edits it.

---

## 0. Read this first: what changes for the paper

1. **There is a new nearest neighbour, and it is closer than Survival Games.** Chacon-Chamorro et al.,
   *Evaluating Cooperative Resilience in Multiagent Systems: A Comparison Between Humans and LLMs*,
   arXiv:2512.11689 (Dec 2025). Human groups and GPT-4 agents play the **same Melting Pot 2.0 Commons
   Harvest substrate** with "interface, rules, and available actions … consistent across conditions", the
   same partial first-person observation, **communication restricted to six categories on hotkeys**, a
   **scripted disruptive bot**, and stochastic resource shocks. Humans with communication sustained the
   resource best, and LLM agents stayed below human levels even with communication. It is not in
   RELATED_WORK.md. It owns *spatial + embodied + humans + LLMs + commons*, so drop spatiality from the
   claim (RELATED_WORK §8 already flags it as the weakest clause), and cite this paper prominently.
2. **The contribution claim survives, but only clause by clause** (detail in §4.1). The clauses that
   still hold are: (a) *individual survival stakes* (death or elimination, which 2512.11689's
   apple-score commons lacks); (b) *deception measured identically for humans and AI*, which C2C
   (arXiv:2604.25088) explicitly says it **could not** do, because its deception rate is inferred from
   agent rationales and "cannot be computed from human gameplay data"; (c) *distinguishability as a function
   of scarcity*, which no screened paper does; (d) *focal-player substitution with seeded co-players*
   (C2C does the substitution, but whole-group designs like 2512.11689 and 2609.30883 do not).
3. **The disclosure reading in RELATED_WORK §7/§8 is too reassuring.** arXiv:2601.20487 bounds its own
   "no label effect" finding to *anonymous aggregate feedback where individual actions can't be
   attributed*. In our game, `share(target)` and messages are attributable, so we are outside that
   boundary. Four other studies find humans do change behaviour toward disclosed AI (§3, T4). Disclosure
   does not break the matched comparison, because both focal arms are told the co-players are
   computer-controlled. It does limit what the human arm measures: *human behaviour toward disclosed bots*,
   not human-human behaviour. Say so in Methods 4.3.
4. **The classifier (N3) needs a guard against trivial distinguishability.** Three papers show
   human/AI detectors latch onto text style, timing/process features, or interface artifacts rather than
   strategy (§3, T6). Report AUC from **action features only** separately from AUC with message-text and
   latency features. Otherwise the scarcity curve may measure typing, not behaviour.
5. **Eight entries in RELATED_WORK.md need a correction before citation**: wrong titles, a scenario
   count taken from the wrong paper, claims stronger than the source supports, or one paper cited for
   something it is not about. See the table in §5.

---

## 1. Research Question

Technical framing (system / method / comparison / metric):

- **System:** multi-agent resource-scarcity or commons games with natural-language communication.
- **Method:** LLM-driven agents, including hybrid RL+LLM.
- **Comparison:** human participants under the same protocol.
- **Metrics:** cooperation, sharing, hoarding, deception, survival, and how distinguishable AI behaviour is from human behaviour.

**Review questions:**
- **RQ1.** Has anyone run a matched-protocol human vs. LLM-agent comparison under resource scarcity, and how closely does it overlap with this project's contribution claim?
- **RQ2.** What does the evidence say about the *direction* and *structure* of human–LLM behavioural divergence in social dilemmas?
- **RQ3.** How is deception measured in human/LLM game studies, and is any measure computed identically for both?
- **RQ4.** What threatens the validity of a human–AI behavioural distinguishability classifier?
- **RQ5.** Does disclosing co-players as AI change human behaviour?

## 2. Search Strategy

Five query families, run on all three databases. Exact strings are in `lit_review_data/search.py`.

| # | Family | arXiv query (abstract field) |
|---|---|---|
| Q1 | Core overlap | (LLM ∨ "language model") ∧ human ∧ (scarcity ∨ commons ∨ "common-pool" ∨ survival ∨ "resource dilemma") |
| Q2 | Matched human/LLM games | (LLM ∨ "language model") ∧ ("human participants" ∨ "human subjects" ∨ "human players" ∨ "human data") ∧ ("social dilemma" ∨ "public goods" ∨ prisoner ∨ "trust game" ∨ cooperation) |
| Q3 | Deception | (LLM ∨ "language model") ∧ (deception ∨ deceptive ∨ lying) ∧ (game ∨ "social dilemma" ∨ negotiation) ∧ human |
| Q4 | Distinguishability | ("Turing test" ∨ distinguishab\* ∨ "human-likeness" ∨ "detect AI") ∧ (LLM ∨ "language model") ∧ (game ∨ behavio\* ∨ agent) |
| Q5 | LLM commons (no human needed) | (LLM ∨ "language model") ∧ (agents ∨ "multi-agent") ∧ ("common-pool" ∨ commons ∨ "resource scarcity" ∨ "scarce resource" ∨ "tragedy of the commons" ∨ sustainability) |

Semantic Scholar used the equivalent bulk-search syntax. OpenAlex used a plain-language query per family, because it has no field-level boolean search.

**Forward citation chasing** (Semantic Scholar) covered every paper citing six seeds: Survival Games
2505.17937, GovSim 2404.16698, Cooperative Resilience 2512.11689, C2C 2604.25088, Collective
cooperation 2606.30454, and Port of Mars 2506.05555.

**Verification of existing entries:** all 30 arXiv IDs in RELATED_WORK.md were resolved against the
arXiv API (title, authors, date, journal-ref, comments) and their abstracts read. The four non-arXiv
entries were resolved via Crossref. Full text was read in targeted passages wherever a claim depended
on something beyond the abstract (§6 lists which).

## 3. Inclusion and Exclusion Criteria

**Include** primary studies, benchmarks, or reviews from 2023 to 2026 that meet any one of these:
- (a) Compare LLM-agent behaviour with human behaviour in a strategic or social-dilemma game, either matched or against published human data.
- (b) Study LLM agents under resource scarcity or commons pressure.
- (c) Measure deception in game play.
- (d) Measure human/AI distinguishability from behaviour.
- (e) Measure how humans react to disclosed AI co-players.

**Exclude** for any of these reasons:
- Wrong population (no human or LLM players).
- Wrong outcome (text judgments, surveys, or modelling human cognition rather than game behaviour).
- Wrong intervention (questionnaires rather than play).
- A duplicate of another version of the same paper.
- Redundant with a stronger included source.
- Outside the date range.

**Automated pre-screen** (stated so it can be reproduced): a record passed only if its title plus abstract
matched all three term groups: an LLM term, a human-participant term, and a game/scarcity/deception term.
The regexes are in `dedup.py`. This step trades recall for feasibility; see §8.

### Screening flow

| Stage | Records | Removed | Note |
|---|---:|---:|---|
| Retrieved (arXiv 972, S2 977, OpenAlex 1,000) | 2,949 | | arXiv Q1/Q4/Q5 capped at 300 by relevance |
| After deduplication | 2,452 | 497 | DOI 124, arXiv ID 304, exact title 62, normalised title 7 |
| After automated pre-screen | 246 | 2,206 | |
| After title screen | 45 new + 8 already in RELATED_WORK | 193 | The 8 rediscovered entries are a recall check |
| After abstract screen | **31 new papers** (33 records) | 12 | 2 papers appeared twice (preprint + journal); reasons in `screening.csv` |
| Citation chasing: 159 citing records → 157 unique → 29 mention humans, ≥2025 | **+1 new** | | arXiv:2609.30883; the other relevant ones were already found |
| Existing RELATED_WORK entries verified | 34 | | + Melting Pot 2.0 added as a correction |
| **Final corpus** | **67** | | |

---

## 4. Evidence Summary

### 4.1 The contribution claim, tested clause by clause (RQ1)

Current claim (RELATED_WORK §8): *"the first matched-protocol human–AI behavioural comparison under
survival-stakes resource scarcity, with a machine-verifiable deception channel, and show that AI-vs-human
distinguishability is itself a measurable, scarcity-dependent quantity."*

| Clause | Closest prior work | Status |
|---|---|---|
| Matched protocol, same action space for humans and AI | C2C 2604.25088 (4-player conquest, 82 matched games); 2606.30454 (networked PD); **2512.11689 (Commons Harvest)**; **2609.30883 (congestion game, 240 + 240 participants)** | **Taken.** Do not claim "first matched-protocol". |
| …under resource scarcity | **2512.11689**: commons with irreversible depletion + shocks, humans vs. LLMs. 2609.30883: scarce road capacity. | **Taken for scarcity in general.** |
| …with *survival stakes* | Port of Mars 2506.05555 (collective survival threshold) compares LLMs only to *published* human metrics; its authors could run only 2 of 4 fidelity tests and **no** social-science Turing test, for lack of parallel human data. Survival Games has no real humans. 2512.11689 scores apples; agents don't die. | **Open**, if "survival stakes" is defined precisely: an individual player is eliminated when their resources run out. Define it in the paper. |
| …focal-player substitution with seeded, scripted co-players | C2C does one-human-seat substitution on fixed starting positions. 2512.11689 and 2609.30883 compare whole groups. | Precedent exists (C2C). Present it as a **design choice with a precedent**, not a novelty. |
| …machine-verifiable deception, computed for both populations | C2C: deception inferred by an LLM judge from agent rationales, "**cannot be computed from human gameplay data**" (Fig. 4). Survival Games: MACHIAVELLI detection, LLM-only. 2608.09574: broken-promise rate, LLM-only. 2512.18292: LLM-as-judge tactic labels. | **Open, and now the strongest clause.** Note that C2C *does* compare **follow-through (promise-keeping) rate** for humans vs. AI, so `promise_break_rate` alone is not new. `deception_rate` from verifiable claims is. |
| Distinguishability as a scarcity-dependent quantity | 2606.30454 (macro/micro dissociation, no environmental manipulation). No screened paper varies an environment parameter and measures distinguishability. | **Open.** |

**Suggested rewording:**
> We contribute a matched-protocol comparison of human participants and LLM agents in a resource-scarcity
> game with individual survival stakes, using focal-player substitution against seeded co-players, in which
> deception is measured identically for both populations through structured, machine-verifiable claims,
> and we show that AI-vs-human behavioural distinguishability varies with scarcity severity.

Cite 2512.11689 and 2609.30883 in the same paragraph as C2C and 2606.30454.

### 4.2 Extraction table: studies with human data (most relevant first)

| Study | Design | Humans / AI | Game | Human data | Key finding | Limitation for our purposes |
|---|---|---|---|---|---|---|
| Chacon-Chamorro et al. 2025, arXiv:2512.11689 (preprint) | Groups, same env/interface/actions; ±communication | Human groups vs. GPT-4 agents (n not extracted; see the supplement on GitHub) | Melting Pot 2.0 Commons Harvest + disruptive RL bot + shocks | Parallel | Humans with communication most resilient; communication helps LLMs but they stay below human levels | No individual survival, deception, or classifier; whole groups |
| O'Neill et al. 2026, arXiv:2604.25088 (preprint) | 1 human + 3 AI; same 82 starting positions replayed AI-only; paired Wilcoxon/McNemar | Students/faculty vs. 6 models (Gemini 3.1, Grok 4.1, GPT) | C2C conquest + private negotiation | Parallel | Humans win more than reference agents (41.5% vs 22.0%), make simpler deals, promise support less (0.063 vs 0.382 per deal), follow through less | Deception not computable for humans; no scarcity |
| Ezaki et al. 2026, arXiv:2609.30883 (preprint) | All-human (12 groups, 240 people), all-agent, mixed (24 groups, 240 people); registered analysis | Humans vs. GPT agents (+2 families) | Two-road congestion | Parallel | A one-sentence warning made GPT populations crowd one road (travel time 64→95 min); humans stayed balanced; in mixed groups humans took the road agents avoided | Scarce capacity, not survival; no communication between players |
| Ferraz de Arruda et al. 2026, arXiv:2606.30454 (preprint) | Same protocol, payoffs, topologies as a published human experiment | 9 open-weight LLMs vs. human data | Networked PD | Published, matched protocol | **One selected model** reproduces macro cooperation trajectory; LLMs underestimate individual heterogeneity; conditional cooperation differs | No scarcity; macro fit is for one model, not all nine |
| Slumbers, Leibo & Janssen 2025, arXiv:2506.05555 (preprint) | LLM-only replication | LLM players vs. published Port of Mars metrics | Collective-risk social dilemma (survival threshold) | Published | LLM simulation of CRSD feasible with SVO personas; only 2/4 fidelity tests possible | Explicitly lacks parallel human data; this is the gap we fill |
| Mutzner, Yasseri & Rauhut 2026, arXiv:2601.20487 (preprint) | 3 humans + 1 bot labelled "human" or "AI" | 236 participants | 4-player repeated PGG + follow-up PD | Parallel | No label effect (TOST, ±5% of endowment) | **Bounded to anonymous aggregate feedback**: individual actions not attributable |
| Dvorak, Stumpf, Fehrler & Fischbacher 2025, *PNAS Nexus* 10.1093/pnasnexus/pgaf112 | Preregistered online experiment | 3,552 participants | Two-player economic games | Parallel | Fairness, trust, trustworthiness, cooperation and coordination **drop when the partner's decision is taken over by ChatGPT**; no drop when people are unsure; people struggle to tell human from AI decisions | Two-player |
| Wang et al. 2026, *National Science Review* 10.1093/nsr/nwag223 (preprint arXiv:2410.03724) | Preregistered; AI personas selfish/cooperative/fair | 1,152 participants | Social dilemma with communication | Parallel | Machine penalty: only *fair* LLM agents get human-level cooperation; fair agents, like humans, sometimes break pre-game promises | Two-player |
| Jiang et al. 2025, arXiv:2507.13524 (preprint) | 3 experiments, hidden vs. disclosed bot identity | 975 participants | Communication-based partner selection | Parallel | Bots more prosocial and *linguistically distinguishable*; disclosure lowers bots' initial selection, then lets them outcompete humans | Partner choice, not scarcity |
| Anwar & Georgalos 2026, arXiv:2603.15852 (preprint) | Lab; chat with GPT-5.2 before each round vs. first round only | 126 participants (+108 human-human benchmark) | Indefinitely repeated PD | Parallel + published | Cooperation with AI plateaus below human-human; **repeated communication has no effect with AI**; human-AI subjects favour Grim Trigger | Two-player |
| Barak & Costa-Gomes 2025, arXiv:2505.11011 (preprint) | Within-subject, incentivised lab | Humans vs. humans or LLMs | Multi-player p-beauty contest | Parallel | Humans choose lower numbers against LLMs, expecting rationality *and cooperation* | Not a dilemma |
| Akata et al. 2025, *Nature Human Behaviour* 10.1038/s41562-025-02172-y | LLM–LLM, LLM–strategy, LLM–human | Human players | Finitely repeated 2×2 games | Parallel | LLMs strong in PD family, weak in coordination (Battle of the Sexes); social chain-of-thought helps with humans | 2×2 abstract |
| Henning et al. (incl. Camerer) 2025, arXiv:2502.15800 (preprint) | Single-model and mixed LLM markets | vs. classic human bubble experiments | Experimental asset market | Published | LLMs price near fundamental value, muted bubbles, lower strategy variance than humans | Market, not dilemma |
| Engel, Großmann & Ockenfels 2025, *Experimental Economics* 10.1017/eec.2025.10038 | oTree toolkit "alter_ego"; machine-only vs. human–machine | Humans + LLMs | Framed PD | Parallel | Framing effects strong among machines but weaker, and qualitatively different, when machines interact with humans | Infrastructure paper; relevant to our mixed design |
| Lei et al. 2024/2026, arXiv:2410.10398 (KDD 2026 oral) | Comparative study | 1,017 participants vs. 10 LLMs | Third-party punishment and other games | Parallel | Mid-capability models over-punish; frontier models converge to human-like leniency | No scarcity |
| Justus & Baber 2025, arXiv:2510.06151 (ECAI 2025) | Grid-world Stag Hunt | 30 participants + 2 experts vs. LLaMA 3.1 / Mixtral | Grid capture game | Parallel | LLMs align with experts more than participants; prompted risk attitudes mirror human variability | Small n |
| Mosquera et al. 2024, arXiv:2403.11381 (preprint) | LLM agents in Melting Pot | GPT-4/3.5 | Commons Harvest | None | Propensity to cooperate, poor collaboration | **LLMs in Melting Pot**: contradicts RELATED_WORK §8 "MARL: no LLMs" |

### 4.3 Studies without human data that matter for framing

| Study | What it gives us |
|---|---|
| GovSim, Piatti et al., NeurIPS 2024, arXiv:2404.16698 | Highest survival rate <54%; communication critical; universalization prompt helps. Metric vocabulary to reuse. |
| SovSim, Borah 2026, arXiv:2605.29062 (single author, under review) | Asymmetric power in an LLM commons, 11 models, up to 87.3% survival degradation. **Claims the asymmetric angle for LLM-only societies**, so our `asymmetric` scenario's novelty is the human comparison, not the asymmetry. |
| RepuNet, Ren et al., AAMAS 2026, arXiv:2505.05029 | Reputation prevents cooperation collapse; framing for `repeated_trust`. |
| CoopEval, Tewolde et al., ICML 2026, arXiv:2604.15267 | 6 LLMs (incl. Claude Sonnet 4.5, GPT 5.2 low-reasoning, Gemini 3 Flash); recent models defect in one-shot dilemmas with or without reasoning; contracting and mediation work best. No human baseline. |
| Gupta et al., AAMAS 2026, arXiv:2510.14401 | CPR without explicit rewards plus social learning and norm punishment; validated by reproducing published human findings. |
| Backmann et al. 2025, arXiv:2505.19212 | Morally charged PD/PGG with a *survival pressure* factor across 9 models; cooperation 7.9–76.3%; game structure and framing are the main causal drivers. Relevant to N1 (dose-response). |
| Seyedin et al. 2026, arXiv:2608.09574 | PGG with managers, elections, private messages; Qwen breaks 13.3% of promises; salaried managers cut private deals. LLM-only broken-promise metric. |
| Dai et al., arXiv:2406.14373 (*Frontiers of Physics* per OpenAlex; confirm) | Sandbox *survival* environment, LLM society moves from conflict to a social contract. LLM-only survival precedent. |
| Survival Games, Chen et al. 2025, arXiv:2505.17937 | See §5. No real humans. |

---

## 5. Verification of RELATED_WORK.md (34 entries)

Legend: ✅ claim supported · ⚠️ partly supported or needs rewording · ❌ wrong as written.
"Abs" = checked against the abstract; "FT" = checked against full text.

| § | Entry | ID / metadata | Claim check | Action |
|---|---|---|---|---|
| 1 | Survival Games, arXiv:2505.17937 | ✅ Chen, Yang, Zhou, Zhang, Lin, Duan (2025) | ✅ FT §4.1: "Human agents follow a rule-based policy derived from [Generative Agents]". ~6 days ✅; survival impact score ✅. ⚠️ Table 1 caption says "GPT-4o as the default model for Owner and NPC decision-making", so the "humans" may themselves be LLM-driven characters. ⚠️ "Ethics prompt eliminates violations" holds only in a one-step evaluation under extreme unfair initialisation. ⚠️ Setup is 2 "humans" + 1 LLM *robot* loyal to an owner, not LLMs vs. humans as peers. | Keep the differentiation. Word it as "no human participants: the human-role agents are simulated", not "scripted policies", since the paper is internally ambiguous. Add the one-step caveat. |
| 2 | GovSim, arXiv:2404.16698 | ✅ NeurIPS 2024 | ✅ Abs. Metric names (survival time, efficiency, equality, over-usage) not checked in FT. | Check metric definitions in FT before mirroring them. |
| 2 | RepuNet, arXiv:2505.05029 | ✅ Ren et al., **AAMAS 2026** | ✅ | Add venue. |
| 2 | SovSim, arXiv:2605.29062 | ✅ Borah, single author, "under review" | ✅ It does claim the asymmetric-power angle (LLM-only). | Answer RELATED_WORK's open question: yes, the angle is claimed for LLM societies. |
| 2 | SRAP-Agent, arXiv:2410.14152 | ✅ | Public *housing* allocation policy simulation; weak relevance. | Drop or cite only in passing. |
| 3 | Akata et al. | ✅ *Nat. Hum. Behav.* 2025, DOI 10.1038/s41562-025-02172-y; arXiv:2305.16867 | ✅ Abs | Add DOI. |
| 3 | LLM traders, arXiv:2502.15800 | ✅ Henning et al. (Camerer last author) | ✅ | — |
| 3 | arXiv:2506.23276 | ❌ Title is **"Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public Goods Games"**, COLM 2025 | ⚠️ FT: PGG *with institutional choice / costly sanctioning*. Human comparison is against **published Gürerk et al. (2006) data**: "convergent outcomes achieved via divergent strategies". The RELATED_WORK paraphrase ("humans use social learning…; LLMs cooperate rigidly") is not the paper's wording. | Fix the title and venue; quote the paper's own finding. |
| 3 | Divergent Minds, arXiv:2605.26437 | ✅ Teo, single author, "theoretical prequel paper" | ✅ FT (PDF): "Fifteen 2022–2026 studies"; direction "LLMs more fair, cooperative, or Nash-converging". ⚠️ The authors say magnitude "is rarely extractable from published abstracts; meta-analytic synthesis … not yet viable", and some table entries are sourced "via WebSearch". | Cite as a narrative synthesis or position, not as evidence. Cite primary studies (Akata; Fontana et al., ICWSM, arXiv:2406.13605) for the direction claim. |
| 3 | IUI 2025, DOI 10.1145/3708359.3712149 | ✅ Sreedhar, Cai, Ma, Nickerson, Chilton; full title "…: Evidence and Mechanisms for AI Agents to Inform Policy Decisions"; arXiv:2502.12504 | ⚠️ **Not supported by the abstract**: it says multi-agent LLMs "successfully replicate human behavior" in PGG treatments. The "direction but not magnitude" framing, if it is in the paper, must be in the full text. | Find the sentence in the full text before quoting; otherwise drop the framing. |
| 3 | Bias-adjusted agents, arXiv:2508.18600 | ✅ Kitadai et al. | ✅ Ultimatum game; responder side improves. | — |
| 3 | Homo Silicus, arXiv:2301.07543 | ⚠️ **Horton, Filippas & Manning** (3 authors); title "…: What Can We Learn from Homo Silicus?" | ✅ | Fix the author list. |
| 4 | Melting Pot, arXiv:2107.06857 | ✅ Leibo et al., ICML 2021 (PMLR) | ❌ "50+ substrates, 256+ scenarios" is **not** in this paper, which reports "over 80 unique test scenarios". The larger counts belong to **Melting Pot 2.0** (Agapiou et al., arXiv:2211.13746), whose abstract gives no counts. | Cite both; take the counts from the MP 2.0 report or the repo, not from memory. |
| 4 | SocialJax, arXiv:2503.14576 | ✅ **ICLR 2026** | ✅ ≥50× speed-up | Add venue. |
| 4 | LLMs in Melting Pot, arXiv:2403.11381 | ✅ | ✅ Commons Harvest | Also fixes the §8 gap table (see below). |
| 4 | Coopetition-Gym, arXiv:2605.02063 | ✅ "v1"; Pant & Yu | MARL, 20 continuous-action environments, no LLMs or humans; little overlap. | Low priority. |
| 5 | Generative Agents, arXiv:2304.03442 | ✅ **UIST 2023**, DOI 10.1145/3586183.3606763 | ✅ | Add venue. |
| 5 | Social norms, IJCAI 2024 | ✅ Ren et al., "…: Principles and Architecture", DOI 10.24963/ijcai.2024/874 | Not checked (venue only). | Add the full citation. |
| 5 | AgentSociety, arXiv:2502.08691 | ✅ | ⚠️ The paper *claims* "alignment … with real-world experimental results", so "scale without a human baseline" is inaccurate as worded. | Reword: "validated against aggregate real-world outcomes, not matched human play". |
| 5 | Static Sandboxes, arXiv:2510.13982 | ✅ | Position/review paper. | Label it as a position paper. |
| 5 | PAVE, arXiv:2605.19351 | ✅ | Rule-violation architecture in a traffic sim; peripheral. | — |
| 5 | arXiv:2603.27771 | ❌ Current (v3) title: **"Emergent Risks in Generative Multi-Agent Systems"** | ✅ Includes competition over shared resources, collusion-like coordination. | Fix the title. |
| 6 | Jones & Bergen | ✅ **PNAS 2026**, DOI 10.1073/pnas.2524472123, "Large language models pass a standard three-party Turing test"; preprint arXiv:2503.23674 | ✅ GPT-4.5 judged human 73% with persona prompt (preprint abstract). | Add DOI and year. |
| 6 | Detect an AI agent, arXiv:2607.26935 | ✅ full title ends "…under **Browser Automation**" | ❌ Not methodologically close to our classifier. It detects Playwright-driven web traffic from mouse-event streams, and the authors say the signal is "a browser-automation artifact, not evidence of agent reasoning". | Re-cast as a **cautionary** citation: detectors can exploit interface artifacts (§3, T6). |
| 6 | Strategy recognition, arXiv:2512.07462 | ✅ Huynh et al. (16 authors) | ✅ FT: ALLC/ALLD/TFT/WSLS classifiers (LR, RF, LSTM) **trained on synthetic noisy IPD trajectories**. | For N9: our action space isn't binary C/D. Define the mapping (e.g. share = C, hoard = D) and report it as an assumption. |
| 6 | arXiv:2605.15473 | ❌ Title: **"Validated Behavioral Hypotheses as a Lens for Evaluating Participant Simulation"** (HumanStudy-Bench) | ✅ | Fix the title. |
| 6 | Deliberate Lab, arXiv:2510.13011 | ✅ | ✅ 12-month deployment, N=9,195 participants | — |
| 7 | C2C, arXiv:2604.25088 | ✅ O'Neill et al. | ✅ FT: 82 human games, matched AI-only replays on the same 82 starting positions, paired tests. **New:** deception is LLM-judged from rationales and not computable for humans; follow-through *is* compared. | Use this as the main support for N2 (§4.1). |
| 7 | Collective cooperation, arXiv:2606.30454 | ✅ | ⚠️ Macro fit is for "**the selected model**", not LLM agents in general. | Reword. |
| 7 | arXiv:2601.20487 | ❌ v3 title: **"Bounded Normative Equivalence in Human-AI Cooperation: Group Behaviour, Not Partner Labels, Predicts Cooperation under Anonymous Aggregate Feedback"** | ⚠️ FT: design is 3 humans + 1 bot labelled human or AI. The finding is **explicitly bounded** to aggregate feedback where individual contributions can't be identified. | Fix the title. Rewrite the Blocker 1 reassurance (see §0.3 and T4). |
| 7 | CoopEval, arXiv:2604.15267 | ✅ **ICML 2026** | ⚠️ Models partly verified (Claude Sonnet 4.5, GPT 5.2, Gemini 3 **Flash**, …); games ✅ PD, Traveler's, Trust, PGG. | Check the full model list in FT §4 before listing it. |
| 7 | Level-k, arXiv:2606.27845 | ✅ Teo, single author; v2 corrected beauty-contest cells | ✅ No last-round defection; PGG contributions flat or rising where humans decay. | Cite v2. |
| 7 | Hierarchical Control, arXiv:2606.20014 | ✅ Hösch et al. | ✅ LLM selects among RL skill policies, 2v2 King of the Hill; plus an n=15 human-likeness perception study. | — |
| 7 | Policy-agnostic teammates, arXiv:2510.06151 | ✅ **ECAI 2025** | ✅ Includes 30 human participants in a grid-world Stag Hunt, i.e. another human/LLM grid-world comparison. | Add to the comparison literature. |

**Gap table (RELATED_WORK §8) needs two fixes:**
- **Row 2**, "LLM-vs-human behavioural games: only 2-player, abstract, no survival stakes": contradicted by 4-player C2C, 4-player PGG (2601.20487), networked PD (2606.30454), 20/50-agent congestion (2609.30883) and the spatial commons (2512.11689). Better: "mostly abstract matrix games; the multi-player/spatial exceptions lack individual survival stakes and a cross-population deception measure".
- **Row 3**, "MARL social dilemmas: no LLMs, no humans": contradicted by 2403.11381 (LLMs in Melting Pot) and 2512.11689 (humans *and* LLMs in Melting Pot).

---

## 6. Thematic Synthesis

**T1. Matched-protocol human/AI comparison is now an established design. Confidence: high.**
Several independent groups converged on it in 2025–26: C2C, 2606.30454, 2512.11689, 2609.30883,
2601.20487, plus older two-player work (Akata; Dvorak et al.; Anwar & Georgalos). Novelty has to come from
*what* is compared and *how it is measured*, not from the design.

**T2. The direction of divergence depends on the game. Confidence: medium.**
In abstract matrix games LLMs are *more* cooperative, fair or Nash-like than humans and less variable:
Fontana et al. (ICWSM, 2406.13605); Akata; Henning et al.; Teo's narrative synthesis (2605.26437);
2608.01193 ("humans are more diverse"). In **dynamic commons**, the sign flips. GovSim finds most LLM
societies fail to sustain the resource, and 2512.11689 finds human groups sustain it better than LLM
agents. This tension is unresolved in the literature, and the scarcity dose-response (N1) is well placed
to address it: *does LLM "niceness" in static games survive dynamic, survival-relevant depletion?* State
it as a hypothesis, with both bodies of evidence cited.

**T3. Aggregate agreement hides individual-level divergence. Confidence: medium-high, mostly preprints.**
Several papers find the same pattern:
- 2606.30454: macro fit, but conditional cooperation rules differ.
- SILICA (2608.28182): agreement "confined to starting points"; no model matches end-state contributions.
- Teo (2606.27845): static level-k play, no belief updating.
- Zheng et al. (2506.09390): human heuristics applied "more rigidly".
- Han et al. (2411.10294): LLMs don't respond to network structure like humans.
- Akata: no adaptation in coordination games.

This supports N3's sharpened hypothesis, and argues for distribution-level and per-round metrics, not only means.

**T4. Disclosed AI identity changes human behaviour when actions are attributable. Confidence: medium-high.**
Evidence that it does:
- Dvorak et al. (PNAS Nexus, n=3,552): cooperation and trust drop when ChatGPT decides.
- The machine penalty (Wang et al., NSR, n=1,152).
- Disclosure dynamics in partner choice (Jiang et al., n=975).
- Communication losing its effect with AI (Anwar & Georgalos).
- Humans expecting rationality from LLMs (Barak & Costa-Gomes).
- Weaker framing effects in human–machine play (Engel et al.).

Evidence that it doesn't: 2601.20487, which is explicitly bounded to non-attributable aggregate feedback.

*Implication:* the human arm measures behaviour toward known bots. That is a valid matched comparison,
because the LLM arm gets the same disclosure, but it is not a measurement of human-human scarcity
behaviour. It also makes N10 (disclosed vs. undisclosed) more valuable than RELATED_WORK suggests.

**T5. Deception measurement is the clearest methodological gap. Confidence: medium.**
Every deception measure found is one of three kinds, none of them computable for both populations:
- **LLM-judged from text or rationales:** C2C; Diplomacy tactics (2512.18292); Survival Games' MACHIAVELLI detector.
- **Promise-breaking in structured games, LLM-only:** 2608.09574; Wang et al. note that fair agents break pre-game promises.
- **Follow-through rates:** these *are* computed for humans (C2C), but measure promise-keeping, not lying.

A structured-claim channel that makes `deception_rate` computable identically for humans and AI is not
present in anything screened.

**T6. Human/AI distinguishability is easy for the wrong reasons. Confidence: medium-high.**
- Text stays "clearly distinguishable" even after calibration (Pagan et al., 2511.04195).
- *Process* features (timing and similar) beat outcome features, with AUC 0.88 at matched performance (Rmus et al., 2605.06524).
- A detector's signal can be pure interface artifact (2607.26935).
- Bots in partner-choice games are "linguistically distinguishable" (Jiang et al.).

*Implication for `classifier.py`:* report three AUC curves (action-only; + message features; + latency).
The scientific claim should rest on the action-only curve. N6 (deliberation rate vs. human latency) should
be reported as its own descriptive finding, not fed into the main classifier.

**T7. Reasoning models cooperate less (N5). Confidence: medium.**
- Corrupted by Reasoning (COLM 2025): o1-series struggle with cooperation.
- CoopEval (ICML 2026): recent models defect in one-shot dilemmas with or without reasoning, so reasoning is not the whole story.
- Kitadai et al. (*Group Decision and Negotiation*, 2406.11426): more reasoning moves behaviour toward theoretical predictions in the ultimatum game.

Including one reasoning and one standard model is well motivated. Expect "more Nash-like", not just "less cooperative".

**T8. Persona and SVO conditioning partly closes gaps (N7). Confidence: low-medium.**
- SVO conditioning improves alignment by up to 70% in a Centipede game (Saponara et al., 2610.01667, Oct 2026), though elicited SVO is prompt- and order-sensitive.
- Persona conditioning helps on the ultimatum responder side (2508.18600).
- Teo (2605.26437) argues persona conditioning hasn't closed the strategic gap.

N7 will add to a live debate rather than confirm something already settled.

**T9. Threats to validity the paper must address. Confidence: medium.**
- **(a) Memorisation of canonical games.** SILICA shows models reproduce memorised results; swapping the listed order of two actions cost one model 58 cooperation points. Our novel game is an asset here: say so. Also **fix and report the action order in LLM prompts** (or randomise it).
- **(b) LLM contamination of online human data.** Anders et al. (*Communications Psychology* 2026) warn that agents can pass as participants. In Velutharambath et al. (2606.04924), 44% of surveyed researchers saw LLM use in crowdsourced data. If Group 1 recruits online rather than in person, add bot and LLM-use defences. The repo doesn't say which mode is planned.
- **(c) Surrogate unreliability in general.** See Wang et al. (2501.08579, review); Gao et al. (2410.19599).

---

## 7. Gaps and Limitations

**Gaps in the literature** (these support the paper):
1. No individual-survival-stakes comparison with real humans.
2. No deception measure computed identically for humans and AI.
3. No study of distinguishability as a function of an environmental parameter.
4. No reconciliation of "LLMs are nicer" (static games) with "LLMs deplete commons" (dynamic games).

**Limitations of this review:**
- **Single reviewer.** No double screening; exclusion decisions are in `screening.csv` for audit.
- **The automated pre-screen favours recall-unsafe precision.** A relevant paper whose abstract doesn't use a human-participant term would be missed. Citation chasing partly compensates.
- **arXiv results capped.** Q1, Q4 and Q5 returned more than 300 hits and only the top 300 by relevance were screened. Q1's arXiv total (1,779) suggests the boolean grouping was looser than intended.
- **Thin citation coverage.** Semantic Scholar lists only 4 papers citing Survival Games and none for 2512.11689, C2C or 2606.30454 (too recent). **Re-run citation chasing before submission.**
- **ACM DL, IEEE Xplore, SSRN and Google Scholar not searched directly.** OpenAlex was used as a proxy.
- **Mostly abstract-level checks.** Full text was read, in targeted passages, for 9 papers only: 2505.17937, 2604.25088, 2512.11689, 2506.05555, 2506.23276, 2604.15267, 2512.07462, 2601.20487, 2605.26437. Everything else is abstract-level.
- **Unverified details.** Sample size for 2512.11689 was not extracted, and the Melting Pot 2.0 substrate/scenario counts were not verified.
- **Mostly preprints.** Most 2026 sources are unreviewed preprints. They are labelled as such in §4, and should be cited as preprints.

**Before submission:**
- Re-run `search.py` (results change weekly in this area).
- Read 2512.11689 and its supplement in full.
- Settle the IUI "direction vs. magnitude" quote.
- Check the GovSim metric definitions and the CoopEval model list.

---

## 8. References

Grouped by role. ★ = must cite. (P) = preprint at time of review.

**Nearest neighbours**
- ★ Chacon-Chamorro, M., Pinzón, J. S., Manrique, R., Giraldo, L. F., & Quijano, N. (2025). Evaluating cooperative resilience in multiagent systems: A comparison between humans and LLMs. arXiv:2512.11689 (P).
- ★ Chen, Z., Yang, Y., Zhou, J., Zhang, Q., Lin, C.-T., & Duan, Y. (2025). Survival Games: Human-LLM strategic showdowns under severe resource scarcity. arXiv:2505.17937 (P).
- ★ O'Neill, A., Zhu, A., Miroyan, M., Norouzi, N., & Gonzalez, J. E. (2026). Cooperate to Compete: Strategic coordination in multi-agent conquest. arXiv:2604.25088 (P).
- ★ Ferraz de Arruda, H., Gracia Lázaro, C., Aleta, A., & Moreno, Y. (2026). Collective cooperation without individual fidelity in LLM agents. arXiv:2606.30454 (P).
- ★ Ezaki, T., et al. (2026). Warned alike, AI agents avoid the less-crowded road while people take it. arXiv:2609.30883 (P).
- Slumbers, O., Leibo, J. Z., & Janssen, M. A. (2025). Using large language models to simulate human behavioural experiments: Port of Mars. arXiv:2506.05555 (P).

**LLM commons / scarcity**
- ★ Piatti, G., Jin, Z., Kleiman-Weiner, M., Schölkopf, B., Sachan, M., & Mihalcea, R. (2024). Cooperate or Collapse: Emergence of sustainable cooperation in a society of LLM agents. NeurIPS 2024. arXiv:2404.16698.
- Borah, A. (2026). Bosses, Kings, and the Commons: Cooperation under power asymmetry in LLM societies. arXiv:2605.29062 (P).
- Ren, S., et al. (2026). Reputation as a solution to cooperation collapse in LLM-based MASs. AAMAS 2026. arXiv:2505.05029.
- Tewolde, E., Zhang, X., Guzman Piedrahita, D., Conitzer, V., & Jin, Z. (2026). CoopEval: Benchmarking cooperation-sustaining mechanisms and LLM agents in social dilemmas. ICML 2026. arXiv:2604.15267.
- Gupta, et al. (2026). The role of social learning and collective norm formation in fostering cooperation in LLM multi-agent systems. AAMAS 2026. arXiv:2510.14401.
- Backmann, et al. (2025). When ethics and payoffs diverge: LLM agents in morally charged social dilemmas. arXiv:2505.19212 (P).
- Seyedin, et al. (2026). The Politician, the Liar, and the Obedient Worker: Emerging behavior of LLM agents in hierarchical games. arXiv:2608.09574 (P).
- Dai, et al. (2024). Artificial Leviathan: Exploring social evolution of LLM agents through the lens of Hobbesian social contract theory. arXiv:2406.14373.
- Huang, Y., et al. (2026). Emergent risks in generative multi-agent systems. arXiv:2603.27771 (P).
- Ji, J., et al. (2024). SRAP-Agent. arXiv:2410.14152 (P).

**Human vs. LLM behaviour in games**
- ★ Akata, Schulz, Coda-Forno, Oh, Bethge, & Schulz (2025). Playing repeated games with large language models. *Nature Human Behaviour*. https://doi.org/10.1038/s41562-025-02172-y
- ★ Horton, J. J., Filippas, A., & Manning, B. S. (2023). Large language models as simulated economic agents: What can we learn from Homo silicus? arXiv:2301.07543.
- Guzman Piedrahita, D., Yang, Y., Sachan, M., Ramponi, G., Schölkopf, B., & Jin, Z. (2025). Corrupted by Reasoning: Reasoning language models become free-riders in public goods games. COLM 2025. arXiv:2506.23276.
- Henning, T., Ojha, S. M., Spoon, R., Han, J., & Camerer, C. F. (2025). LLM agents do not replicate human market traders. arXiv:2502.15800 (P).
- Fontana, N., Pierri, F., & Aiello, L. M. (2024). Nicer than humans: How do large language models behave in the prisoner's dilemma? ICWSM. arXiv:2406.13605.
- Teo, P. H. (2026). Divergent minds, convergent baselines. arXiv:2605.26437 (P; theoretical).
- Teo, P. H. (2026). LLM agents as static level-k players in behavioural games. arXiv:2606.27845v2 (P).
- Tareaf (2026). Benchmarking large language model agent societies against human behavioural distributions (SILICA). arXiv:2608.28182 (P).
- Zheng, et al. (2025). Beyond Nash equilibrium: Bounded rationality of LLMs and humans in strategic decision-making. arXiv:2506.09390 (P).
- Han, et al. (2024). Static network structure cannot stabilize cooperation among LLM agents. *PLoS ONE*. arXiv:2411.10294.
- Pal, et al. (2026). Large language models instantiate evolutionarily robust strategies of cooperation. *PNAS Nexus*. https://doi.org/10.1093/pnasnexus/pgag210
- Palatsi, et al. (2025). Large language models replicate and predict human cooperation across experiments in game theory. arXiv:2511.04500 (P).
- Xie, C., et al. (2024). Can large language model agents simulate human trust behavior? NeurIPS 2024. arXiv:2402.04559.
- Lei, et al. (2026). Are LLMs socially adaptive? Contrasting belief evolution in LLMs and humans. KDD 2026. arXiv:2410.10398.
- Pham, et al. (2026). Humans are more diverse: Frontier LLMs show extreme policies in idealised AI development races. arXiv:2608.01193 (P).
- Sreedhar, Cai, Ma, Nickerson, & Chilton (2025). Simulating cooperative prosocial behavior with multi-agent LLMs: Evidence and mechanisms for AI agents to inform policy decisions. IUI 2025. https://doi.org/10.1145/3708359.3712149
- Justus, A. A., & Baber, C. (2025). LLMs as policy-agnostic teammates. ECAI 2025. arXiv:2510.06151.
- Kitadai, A., Fukasawa, Y., & Nishino, N. (2025). Bias-adjusted LLM agents for human-like decision-making via behavioral economics. arXiv:2508.18600 (P).
- Kitadai, A., et al. (2025). Can AI with high reasoning ability replicate human-like decision making in economic experiments? *Group Decision and Negotiation*. https://doi.org/10.1007/s10726-025-09946-9
- Saponara, et al. (2026). Conditioning LLMs on social value orientation improves behavioural alignment in a sequential social dilemma. arXiv:2610.01667 (P).
- Huynh, T.-K., et al. (2025). Understanding LLM agent behaviours via game theory. arXiv:2512.07462 (P).
- Liu, X., et al. (2026). Validated behavioral hypotheses as a lens for evaluating participant simulation. arXiv:2605.15473 (P).

**Humans reacting to AI co-players (disclosure)**
- ★ Dvorak, Stumpf, Fehrler, & Fischbacher (2025). Adverse reactions to the use of large language models in social interactions. *PNAS Nexus*. https://doi.org/10.1093/pnasnexus/pgaf112
- ★ Mutzner, N., Yasseri, T., & Rauhut, H. (2026). Bounded normative equivalence in human-AI cooperation: Group behaviour, not partner labels, predicts cooperation under anonymous aggregate feedback. arXiv:2601.20487v3 (P).
- Wang, et al. (2026). LLM agents overcome the machine penalty when acting fairly but not when acting selfishly or altruistically. *National Science Review*. https://doi.org/10.1093/nsr/nwag223
- Jiang, et al. (2025). Humans learn to prefer trustworthy AI over human partners. arXiv:2507.13524 (P).
- Anwar & Georgalos (2026). Playing against the machine: Cooperation, communication, and strategy heterogeneity in repeated prisoner's dilemma. arXiv:2603.15852 (P).
- Barak & Costa-Gomes (2025). Humans expect rationality and cooperation from LLM opponents in strategic games. arXiv:2505.11011 (P).
- Engel, Großmann, & Ockenfels (2025). Integrating machine behavior into human subject experiments. *Experimental Economics*. https://doi.org/10.1017/eec.2025.10038

**Deception**
- Li, et al. (2025). Measuring fine-grained negotiation tactics of humans and LLMs in Diplomacy. arXiv:2512.18292 (P).
- (See also C2C, Survival Games and Seyedin et al. above.)

**Distinguishability / Turing tests**
- ★ Jones & Bergen (2026). Large language models pass a standard three-party Turing test. *PNAS*. https://doi.org/10.1073/pnas.2524472123 (preprint arXiv:2503.23674)
- Pagan, et al. (2025). Computational Turing test reveals systematic differences between human and AI language. arXiv:2511.04195 (P).
- Rmus, et al. (2026). Process matters more than output for distinguishing humans from machines. arXiv:2605.06524 (P).
- Choudhary, V., et al. (2026). What does it take to detect an AI agent? Minimal feature sets for behavioral detection under browser automation. arXiv:2607.26935 (P; workshop).

**Environments and platforms**
- ★ Leibo, J. Z., et al. (2021). Scalable evaluation of multi-agent reinforcement learning with Melting Pot. ICML 2021. arXiv:2107.06857.
- Agapiou et al. (2022). Melting Pot 2.0. arXiv:2211.13746.
- Mosquera, M., et al. (2024). Can LLM-augmented autonomous agents cooperate? An evaluation of their cooperative capabilities through Melting Pot. arXiv:2403.11381.
- Guo, Z., et al. (2026). SocialJax. ICLR 2026. arXiv:2503.14576.
- Pant, V., & Yu, E. (2026). Coopetition-Gym v1. arXiv:2605.02063 (P).
- Qian, C., et al. (2025). Deliberate Lab: A platform for real-time human-AI social experiments. arXiv:2510.13011.
- Hösch, J., et al. (2026). Hierarchical control in multi-agent games: LLM-based planning and RL execution. arXiv:2606.20014 (P).

**Generative agent societies**
- ★ Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. UIST 2023. https://doi.org/10.1145/3586183.3606763
- Ren, Cui, Song, Wang, & Hu (2024). Emergence of social norms in generative agent societies: Principles and architecture. IJCAI 2024. https://doi.org/10.24963/ijcai.2024/874
- Piao, J., et al. (2025). AgentSociety. arXiv:2502.08691.
- Chen, J., Badshah, S., Yu, X., & Han, S. (2025). Static sandboxes are inadequate. arXiv:2510.13982 (P; position).
- Yehia, A., et al. (2026). PAVE. arXiv:2605.19351 (P).

**Validity of LLM surrogates and human data**
- Wang, et al. (2025). LLM-based human simulations have not yet been reliable. arXiv:2501.08579 (P; review).
- Gao, et al. (2024). Take caution in using LLMs as human surrogates: Scylla ex machina. arXiv:2410.19599 (P).
- Anders, Buder, Papenmeier, & Huff (2026). How online studies must increase their defences against AI. *Communications Psychology*. https://doi.org/10.1038/s44271-025-00388-2
- Velutharambath, et al. (2026). Can crowdsourcing survive the LLM era? arXiv:2606.04924 (P).
- Mu, et al. (2024). Multi-agent, human-agent and beyond: A survey on cooperation in social dilemmas. arXiv:2402.17270 (survey).

*Initials are given only where the arXiv metadata supplied full names; entries with surnames only came from Crossref/OpenAlex. Author lists shortened to "et al." are complete in the arXiv/Crossref metadata. Pull full
BibTeX from arXiv or Crossref when building `references.bib`; don't retype from this list.*

---

## 9. Search Log

| Database | Date searched | Query family | Filters | Total hits | Retrieved |
|---|---|---|---|---:|---:|
| arXiv API | 2026-10-06 | Q1-core | submittedDate 2023-01-01–2026-10-06 | 1,779 | 300 |
| Semantic Scholar | 2026-10-06 | Q1-core | year 2023–2026 | 731 | 731 |
| OpenAlex | 2026-10-06 | Q1-core | pub. date 2023-01-01–2026-10-06 | 323 | 200 |
| arXiv API | 2026-10-06 | Q2-matched | as above | 26 | 26 |
| Semantic Scholar | 2026-10-06 | Q2-matched | as above | 23 | 23 |
| OpenAlex | 2026-10-06 | Q2-matched | as above | 1,036 | 200 |
| arXiv API | 2026-10-06 | Q3-deception | as above | 46 | 46 |
| Semantic Scholar | 2026-10-06 | Q3-deception | as above | 81 | 81 |
| OpenAlex | 2026-10-06 | Q3-deception | as above | 1,812 | 200 |
| arXiv API | 2026-10-06 | Q4-distinguish | as above | 810 | 300 |
| Semantic Scholar | 2026-10-06 | Q4-distinguish | as above | 107 | 107 |
| OpenAlex | 2026-10-06 | Q4-distinguish | as above | 1,933 | 200 |
| arXiv API | 2026-10-06 | Q5-llm-commons | as above | 1,373 | 300 |
| Semantic Scholar | 2026-10-06 | Q5-llm-commons | as above | 35 | 35 |
| OpenAlex | 2026-10-06 | Q5-llm-commons | as above | 552 | 200 |
| Semantic Scholar citations | 2026-10-06 | Forward citations of 6 seeds | — | 159 (4 / 148 / 0 / 0 / 0 / 7) | all |
| arXiv API (id_list) | 2026-10-06 | Verification of 30 + 32 IDs | — | 62 | 62 |
| Crossref | 2026-10-06 | Verification of 10 DOIs / titles | — | — | — |

OpenAlex "total hits" are relevance-ranked full-text matches; most of the long tail is off-topic, which is why only the top 200 were retrieved.
