::: {align="center"}
# Behavioral Divergence Under Scarcity

### Do LLM-driven multi-agent societies behave like humans when shared resources run out?

**A controlled Common Pool Resource (CPR) simulation comparing human
decisions with a hybrid PPO + LLM agent under resource scarcity.**

`<br/>`{=html}

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Research](https://img.shields.io/badge/Research-Multi--Agent%20Systems-6C5CE7)
![Focus](https://img.shields.io/badge/Focus-Scarcity%20%7C%20Cooperation%20%7C%20Alignment-00897B)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)
:::

------------------------------------------------------------------------

## Overview

**Behavioral Divergence Between LLM-Driven Multi-Agent Societies and
Humans Under Resource Scarcity** investigates whether autonomous AI
agents reproduce human social behavior when essential shared resources
become scarce.

The project models a small society sharing a limited freshwater
resource. It compares human participants with a hybrid AI agent while
keeping the other agents' policies and random seeds matched across
experimental conditions. This *focal-player substitution* design aims to
make differences in cooperation, hoarding, sharing, deception,
inequality, and survival easier to attribute to the focal
decision-maker.

The central question is:

> **When survival is at stake, do AI agents make the same social
> trade-offs as humans---or do they follow a fundamentally different
> strategy?**

## Why this matters

Multi-agent AI systems may eventually support resource allocation,
emergency logistics, infrastructure coordination, and other settings
where individual decisions affect a shared pool. Strong performance in
ordinary tasks does not automatically mean an agent will behave
appropriately during a crisis.

This project uses a controlled scarcity environment to study the gap
between **human social decision-making** and **LLM-driven agent
behavior**, with a focus on measurable actions rather than subjective
interpretation alone.

## Research questions

-   **Cooperation:** How does resource sharing change as scarcity
    intensifies?
-   **Hoarding:** Do agents preserve resources defensively or continue
    drawing from the commons?
-   **Communication integrity:** Can resource claims be checked against
    the environment's ground truth?
-   **Fairness:** How do human and AI societies differ in resource
    inequality?
-   **Resilience:** Which societies survive a drought shock?
-   **Behavioral distinguishability:** Can recorded trajectories reveal
    whether a focal decision-maker was human or AI?

## System at a glance

``` mermaid
flowchart TD
    A[Common Pool Resource Environment] --> B[Four Fixed Policy Agents]
    A --> C[Focal Player]
    C --> D1[Human Participant]
    C --> D2[Hybrid AI Agent]
    D2 --> E[PPO Reflex Policy]
    D2 --> F[LLM Deliberation on High-Stakes Events]
    B --> G[Matched Experimental Trials]
    D1 --> G
    E --> G
    F --> G
    G --> H[Action and Resource Logs]
    H --> I[Statistical Comparison]
    H --> J[Behavioral Classifier]
    I --> K[Cooperation, Inequality, Survival and Deception Analysis]
    J --> K
```

## Environment and experimental design

### Shared-resource dynamics

The simulation represents five agents sharing a central freshwater lake.

  -----------------------------------------------------------------------
  Parameter                           Specification
  ----------------------------------- -----------------------------------
  Agents                              5 per society

  Survival cost                       2 water units per agent per round

  Gather action                       +3 water units before
                                      resource-allocation constraints

  Carrying capacity                   (K = 50.0)

  Intrinsic growth rate               (r = 0.35)

  Resource regeneration               Logistic growth minus aggregate
                                      demand

  Over-demand handling                Harvest is proportionally scaled
                                      when total demand exceeds available
                                      stock
  -----------------------------------------------------------------------

The resource stock follows:

\[
S\_{t+1}=S_t+rS_t`\left`{=tex}(1-`\frac{S_t}{K}`{=tex}`\right`{=tex})-D_t
\]

When total demand exceeds available stock, each agent's granted harvest
is scaled proportionally:

\[ Y_i=D_i`\frac{S_t}{D_t}`{=tex} \]

### Available actions

-   `gather` --- request a harvest from the shared resource.
-   `share(target, amount)` --- transfer water to another agent.
-   `hoard` --- preserve or ration personal reserves without drawing
    from the lake.
-   `skip` --- take no action.
-   `communicate(target, message)` --- send a structured message to
    another agent.

### Matched focal-player substitution

Four non-focal seats use fixed policies: **Cooperator, Free-Rider,
Tit-for-Tat, and Random**. Across matched trials, the fifth seat is
substituted between a human participant and the hybrid AI agent, with
matched random seeds intended to reduce unrelated variation.

### Hybrid AI architecture

-   **Reflex layer:** a Proximal Policy Optimization (PPO) policy for
    routine action selection.
-   **Deliberation layer:** an LLM invoked for selected high-stakes
    social events, such as resource crises, drought shocks, or incoming
    gifts.
-   **Fallback chain:** the project dossier describes a provider
    fallback path through Groq, Gemini, OpenRouter, and local Ollama.
    Availability and configuration depend on the deployment environment.

## Reported results

The current research dossier reports **84 trials** (24 human and 60 AI)
and **5,320 recorded action decisions**. The values below are reported
project results and should be independently revalidated against the raw
logs and analysis scripts before publication.

  -------------------------------------------------------------------------------
  Measure                        Human                   AI Reported test
  --------------- -------------------- -------------------- ---------------------
  Pooled                  0.251 ± 0.13         0.158 ± 0.05 (U=963.0, p=0.0151)
  cooperation                                               
  rate                                                      

  Pooled water             8.12 ± 9.73          5.63 ± 3.63 (U=936.0, p=0.0306)
  shared                                                    

  Society Gini            0.266 ± 0.17         0.108 ± 0.05 (U=972.5, p=0.0096)
  inequality                                                

  Pooled                  0.125 ± 0.34         0.000 ± 0.00 (U=810.0, p=0.0058)
  deception rate                                            

  Decision                    1,759 ms                 0 ms (p\<0.0001)
  latency                                                   

  Drought-shock           0.138 ± 0.10         0.046 ± 0.04 (U=215.5, p=0.0037)
  hoarding                                                  

  Drought-shock           0.611 ± 0.40         1.000 ± 0.00 (U=70.0, p=0.0006)
  society                                                   
  survival                                                  
  -------------------------------------------------------------------------------

The dossier also reports a Random Forest trajectory classifier with
**91.7% accuracy**, **0.940 ROC-AUC**, and **0.837 F1** using five-fold
stratified cross-validation. These results are descriptive of the
reported experiment, not a guarantee of performance on new populations,
environments, or agent configurations.

### Scarcity dose-response

The reported analysis describes different responses as scarcity
increases:

-   **Sharing:** human sharing decreases more steeply than AI sharing.
-   **Hoarding:** human hoarding increases with scarcity, while the AI
    trend is reported in the opposite direction.
-   **Communication:** the experiment audits structured resource claims
    against environment state, allowing a claim to be checked without
    relying solely on subjective annotation.

These patterns motivate further investigation; they should not be
interpreted as universal claims about all humans or all AI models.

## Technology and methods

The project dossier identifies the following methods and components:

-   **Multi-agent simulation:** shared-resource environment and fixed
    behavioral policies.
-   **Reinforcement learning:** PPO reflex policy.
-   **LLM deliberation:** provider-based reasoning for selected
    high-stakes events.
-   **Data logging:** SQLite action-trial records.
-   **Statistical analysis:** Mann--Whitney U tests, p-values, Cliff's
    delta, and Cohen's d where reported.
-   **Behavioral analysis:** Random Forest and Logistic Regression
    baselines, cross-validation, and feature-importance analysis.
-   **Reproducibility controls:** matched random seeds and focal-player
    substitution.

> **Implementation note:** Exact package versions, setup commands, API
> variable names, and entry-point scripts were not specified in the
> supplied research dossier. Add the repository's verified commands and
> dependency versions before publishing this README as an executable
> setup guide.

## Repository structure

A suggested structure for organizing the research code is shown below.
Rename or remove entries to match the actual repository.

``` text
.
├── README.md
├── data/
│   └── llm_sft_dataset.jsonl
├── environment/
│   └── scarcity_env.py
├── agents/
│   ├── ppo_policy.py
│   └── llm_deliberator.py
├── experiments/
│   └── run_trials.py
├── analysis/
│   ├── statistical_tests.py
│   └── behavior_classifier.py
├── results/
│   ├── figures/
│   └── tables/
└── requirements.txt
```

## Getting started

The supplied project brief does not include a verified repository URL,
dependency lockfile, or executable entry point. To avoid inventing
commands that may not work, use the following checklist to complete this
section for your actual codebase:

1.  Install the Python version and dependencies specified by the
    project.
2.  Configure any required LLM provider credentials using environment
    variables; **never commit API keys**.
3.  Run a small environment smoke test before launching a full
    experiment.
4.  Execute the experiment script with a documented random seed.
5.  Save raw trial logs separately from processed analysis outputs.
6.  Run the statistical analysis and classifier on the saved logs.
7.  Record package versions, configuration, seed values, and dataset
    provenance for each run.

Example `.env` pattern (use only variable names supported by your
implementation):

``` bash
# Store real credentials locally; do not commit this file.
LLM_API_KEY=your_key_here
```

Add `.env`, secrets, local databases, and private participant data to
`.gitignore` where appropriate.

## Reproducibility and responsible reporting

For credible research and reproducible results:

-   Publish the environment rules and agent policies used in each
    experiment.
-   Keep human and AI trial inclusion criteria explicit.
-   Report the number of independent participants and trials separately
    from the number of action decisions.
-   Document exclusions, missing data, random seeds, and model/provider
    versions.
-   Include confidence intervals and effect sizes alongside significance
    tests.
-   Avoid treating individual trial transcripts as representative of all
    human or AI behavior.
-   Protect participant privacy and obtain appropriate consent for
    human-subject data.
-   Clearly distinguish measured outcomes, interpretations, and future
    hypotheses.

## Limitations

-   The reported sample contains 24 human trials and 60 AI trials;
    broader validation is needed.
-   A five-agent simulated commons cannot capture every feature of
    real-world resource allocation.
-   Results may depend on the chosen LLM, prompts, PPO training, fixed
    companion policies, and interface.
-   Zero reported AI deception in this setup does not prove that AI
    systems cannot deceive in other settings.
-   Reported classifier performance requires validation on held-out
    scenarios and independent datasets to assess generalization.
-   Statistical values should be checked against the underlying raw data
    and analysis pipeline before submission or external claims.

## Future work

-   Expand human participation and test across multiple demographic and
    contextual groups.
-   Evaluate additional LLMs, prompt strategies, and
    reinforcement-learning policies.
-   Test different scarcity intensities, resource regeneration rates,
    and companion-agent mixtures.
-   Validate trajectory classifiers on unseen seeds and altered
    environments.
-   Explore supervised fine-tuning and in-context learning using
    ethically collected human decision trajectories.
-   Investigate interventions that improve crisis-time cooperation
    without sacrificing individual safety.

## Authors and affiliation

**Research mentor:** Ms. Laxmi --- Assistant Professor

**Student researchers:** - Utkarsh Pandey - Sujal Kumar - Saksham
Singh - Yashash Tyagi

**Department:** Computer Science and Engineering (AI & ML)\
**Institution:** KIET Deemed to be University, Ghaziabad, Uttar Pradesh,
India

## Citation

If you use this work, cite the research paper once a stable publication
or preprint is available. Until then, replace the placeholder below with
the actual DOI, preprint URL, or repository citation:

``` text
Pandey, U., Kumar, S., Singh, S., Tyagi, Y., and Laxmi.
“Behavioral Divergence Between LLM-Driven Multi-Agent Societies
and Humans Under Resource Scarcity.” Unpublished manuscript.
```

## Acknowledgements

The project is developed as an academic research effort within the
Department of Computer Science and Engineering (AI & ML), KIET Deemed to
be University.

------------------------------------------------------------------------

::: {align="center"}
**Studying not only what autonomous agents decide---but how scarcity
changes the society around them.**
:::
