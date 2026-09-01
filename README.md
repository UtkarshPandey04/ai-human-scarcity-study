Step 1: Everyone clones it locally:

git clone https://github.com/<your-org-or-username>/ai-human-scarcity-study.git
cd ai-human-scarcity-study

-----------------------------------------------------------------------------------------

step 2:Everyone else then pulls this before creating their own branch:

bash
git pull origin main

-----------------------------------------------------------------------------------------

step 3:Branching strategy

Keep it simple — you don't need a complex Git-flow setup for a 4-person student project. Use this structure:

main                    → always stable, working code only
├── group1-human-study  → Sujal & Utkarsh's long-lived working branch
├── group2-agents        → Yashash & Saksham's long-lived working branch

---------------------------------------------------------------------------------------------
Already done by me:
Creating the two group branches (repo owner runs this once)
bash
git checkout -b group1-human-study
git push origin group1-human-study

git checkout main
git checkout -b group2-agents
git push origin group2-agents

--------------------------------------------------------------------------------------------
Each person's daily workflow
bash
# Sujal or Utkarsh, working on human study:
git checkout group1-human-study
git pull origin group1-human-study
# ... do work ...
git add .
git commit -m "Add consent screen to Streamlit app"
git push origin group1-human-study
bash
# Yashash or Saksham, working on agents:
git checkout group2-agents
git pull origin group2-agents
# ... do work ...
git add .
git commit -m "Implement drought event in environment.py"
git push origin group2-agents

------------------------------------------------------------------------------------------

Step 4: Merging into main

Don't merge straight to main without review — even in a student project, this catches bugs early and gives your guide/reviewers a clean history.

When a group's feature is stable (e.g., "environment + RL policy working end to end"), open a Pull Request: group2-agents → main
The other group reviews it (Yashash/Saksham review Group 1's PRs and vice versa) — this also forces everyone to actually understand both halves of the project, which helps a lot during your viva/defense
Merge once approved
bash
# After PR is approved and merged on GitHub, everyone syncs:
git checkout main
git pull origin main


-------------------------------------------------------------------------------------------------------
Step 5: The critical shared file — LOGGING_SCHEMA.md

Since both branches depend on this file matching exactly, treat it specially:

Finalize it together in your Week 1 meeting
Commit it to main directly (not to either group branch) before other work starts
Both groups pull it into their branch immediately:
bash
git checkout group1-human-study
git merge main
git checkout group2-agents
git merge main
If it ever needs changing later, both groups must agree in a call first — a silent schema change on one branch will break the other group's logs silently, which is the most common integration bug in projects like this.

------------------------------------------------------------------------------------------------------
 step 6:: When Phase 3 (Joint Analysis) starts (Week 8+)

Create a third shared branch since both groups now work together on the same files:

bash
git checkout main
git checkout -b joint-analysis
git push origin joint-analysis

All 4 members work here for feature extraction, stats, classifier, and dashboard — since this phase genuinely needs both groups' data and no group "owns" it.

-------------------------------------------------------------------------------------------------------

Quick reference: full branch lifecycle
main
 ├── group1-human-study   (Weeks 1–7) → PR into main once human study logging is validated
 ├── group2-agents         (Weeks 1–7) → PR into main once AI trial logging is validated
 └── joint-analysis        (Weeks 8–10) → PR into main once analysis + dashboard are done
