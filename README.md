

# 🚀 AI Human Scarcity Study — Git & Branching Workflow

This document defines the GitHub workflow for our **4-person student research project**. The goal is to keep collaboration simple, avoid conflicts, and ensure that `main` always contains stable, working code.

---

## 📌 Team Branch Structure

We will use **3 main branches** throughout the project:

```text
main
│
├── group1-human-study
│   └── Sujal + Utkarsh
│
├── group2-agents
│   └── Yashash + Saksham
│
└── joint-analysis
    └── All 4 members — Phase 3
```

### Branch Responsibilities

| Branch               | Members           | Purpose                                                | Timeline       |
| -------------------- | ----------------- | ------------------------------------------------------ | -------------- |
| `main`               | Everyone          | Stable, reviewed code                                  | Entire project |
| `group1-human-study` | Sujal + Utkarsh   | Human study / participant-side work                    | Weeks 1–7      |
| `group2-agents`      | Yashash + Saksham | AI agents / environment / RL work                      | Weeks 1–7      |
| `joint-analysis`     | Everyone          | Feature extraction, statistics, classifier & dashboard | Weeks 8–10     |

> ⚠️ **Rule:** Never push experimental or broken code directly to `main`.

---

# 1️⃣ Clone the Repository

Everyone should first clone the repository to their local machine.

```bash
git clone https://github.com/<your-org-or-username>/ai-human-scarcity-study.git
cd ai-human-scarcity-study
```

Verify the repository:

```bash
git remote -v
```

---

# 2️⃣ Sync With `main`

Before creating or switching to your working branch, make sure your local repository is up to date.

```bash
git checkout main
git pull origin main
```

### Why?

This ensures everyone starts their work from the **latest stable version** of the project.

---

# 3️⃣ Branching Strategy

We are keeping the branching strategy intentionally simple.

```text
main
│
├── group1-human-study
│   ├── Sujal
│   └── Utkarsh
│
└── group2-agents
    ├── Yashash
    └── Saksham
```

### `main`

* Always stable
* Contains reviewed and working code
* No direct feature development

### `group1-human-study`

Used by **Sujal & Utkarsh** for:

* Human study implementation
* Participant interaction
* Consent screens
* Study logging
* Streamlit UI
* Human-trial related functionality

### `group2-agents`

Used by **Yashash & Saksham** for:

* AI agent implementation
* Environment development
* RL policies
* Drought/scarcity events
* Agent trial logging

---

# 4️⃣ Create the Group Branches

### ✅ Already completed by the repository owner

The two long-lived group branches have already been created:

```bash
git checkout -b group1-human-study
git push origin group1-human-study

git checkout main

git checkout -b group2-agents
git push origin group2-agents
```

After this, everyone should be able to see both branches on GitHub.

Check available branches:

```bash
git branch -a
```

---

# 5️⃣ Daily Workflow

## 👥 Group 1 — Human Study

**Sujal & Utkarsh**

Before starting work:

```bash
git checkout group1-human-study
git pull origin group1-human-study
```

Then work normally.

After completing a logical piece of work:

```bash
git add .
git commit -m "Add consent screen to Streamlit app"
git push origin group1-human-study
```

### Example

```text
Start work
    ↓
checkout group1-human-study
    ↓
pull latest changes
    ↓
write code
    ↓
test locally
    ↓
git add .
    ↓
git commit
    ↓
git push
```

---

## 🤖 Group 2 — AI Agents

**Yashash & Saksham**

Before starting work:

```bash
git checkout group2-agents
git pull origin group2-agents
```

After completing a logical piece of work:

```bash
git add .
git commit -m "Implement drought event in environment.py"
git push origin group2-agents
```

---

# 6️⃣ Write Good Commit Messages

Keep commit messages **short, specific, and meaningful**.

### ✅ Good

```text
Add consent screen to Streamlit app
Implement drought event in environment
Fix agent reward calculation
Add participant logging
Update scarcity environment
Add trial data validation
```

### ❌ Avoid

```text
changes
update
final
test
working
done
asdf
```

### Recommended format

```text
<action> <what was changed>
```

Examples:

```text
Add participant consent flow
Fix resource allocation logic
Implement RL reward function
Update trial logging schema
```

---

# 7️⃣ 🔐 Critical Shared File — `LOGGING_SCHEMA.md`

`LOGGING_SCHEMA.md` is a **shared dependency between both groups**.

Both sides must produce logs using the **same schema**.

Therefore, this file needs special handling.

### Step 1 — Finalize it together

During the **Week 1 team meeting**, all 4 members should agree on:

* Required fields
* Data types
* Naming conventions
* Trial IDs
* Participant IDs
* Agent IDs
* Event formats
* Timestamps
* Output structure

---

### Step 2 — Commit it to `main`

Once finalized:

```bash
git checkout main
git add LOGGING_SCHEMA.md
git commit -m "Finalize logging schema"
git push origin main
```

---

### Step 3 — Sync both branches

Group 1:

```bash
git checkout group1-human-study
git merge main
git push origin group1-human-study
```

Group 2:

```bash
git checkout group2-agents
git merge main
git push origin group2-agents
```

Now both groups are working with the **exact same schema**.

> ⚠️ **Important:** Never silently change `LOGGING_SCHEMA.md` on only one branch.

If the schema needs to change later, **all 4 members should agree first**.

---

# 8️⃣ 🔄 Keep Your Branch Updated

While working for several days, `main` may receive updates from the other group.

Before starting a new task, sync your branch:

```bash
git checkout group1-human-study
git pull origin group1-human-study
git merge main
```

For Group 2:

```bash
git checkout group2-agents
git pull origin group2-agents
git merge main
```

Resolve any conflicts locally, test everything, and then push.

---

# 9️⃣ 🔀 Merging Into `main`

**Do not directly merge your branch into `main` without review.**

When your group's feature is stable:

### Example

Group 2 completes:

```text
Environment
      +
RL Policy
      +
AI Trial Logging
      ↓
Working End-to-End
```

Create a Pull Request on GitHub:

```text
group2-agents → main
```

---

## 👀 Cross-Review System

To make sure everyone understands the complete project:

| PR Author | Reviewers         |
| --------- | ----------------- |
| Group 1   | Yashash + Saksham |
| Group 2   | Sujal + Utkarsh   |

This isn't just for code quality — it also means everyone gets familiar with the **other half of the project**, which is extremely useful during the **viva, demo, and research defense**.

### PR workflow

```text
Complete feature
      ↓
Test locally
      ↓
Push branch
      ↓
Create Pull Request
      ↓
Other group reviews
      ↓
Changes requested? ── Yes → Fix → Push again
      ↓ No
PR approved
      ↓
Merge into main
```

---

# 🔟 After a PR Is Merged

Everyone should synchronize their local repository.

```bash
git checkout main
git pull origin main
```

Then update your working branch.

### Group 1

```bash
git checkout group1-human-study
git merge main
git push origin group1-human-study
```

### Group 2

```bash
git checkout group2-agents
git merge main
git push origin group2-agents
```

---

# 1️⃣1️⃣ Phase 3 — Joint Analysis

Starting around **Week 8**, both groups will begin working on the same research pipeline.

At this point, create a dedicated shared branch:

```text
joint-analysis
```

Create it from the latest `main`:

```bash
git checkout main
git pull origin main

git checkout -b joint-analysis
git push origin joint-analysis
```

---

## 🧠 What Goes Into `joint-analysis`?

All 4 members collaborate on:

```text
Human Study Data
       +
AI Agent Data
       ↓
Data Cleaning
       ↓
Feature Extraction
       ↓
Statistical Analysis
       ↓
ML Classifier
       ↓
Visualization
       ↓
Dashboard
       ↓
Research Findings
```

Typical work includes:

* Feature extraction
* Statistical testing
* Human vs AI comparison
* Classification
* Behavioral analysis
* Visualization
* Dashboard development
* Final research analysis

---

# 📅 Full Project Timeline

```text
WEEK 1
│
├── Finalize LOGGING_SCHEMA.md
├── Set up repository
├── Create branches
└── Begin development
│
│
WEEKS 1–7
│
├── Group 1 → Human Study
│
└── Group 2 → AI Agents
│
│
WEEK 7
│
├── Validate human-study logging
├── Validate AI-agent logging
└── Merge stable features into main
│
│
WEEK 8
│
└── Create joint-analysis branch
│
│
WEEKS 8–10
│
├── Feature Extraction
├── Statistical Analysis
├── ML Classifier
├── Dashboard
└── Final Research Analysis
│
│
FINAL
│
└── PR → main
```

---

# ⚡ Quick Reference

### 🧑‍💻 Group 1

```bash
git checkout group1-human-study
git pull origin group1-human-study

# Work...

git add .
git commit -m "Describe your change"
git push origin group1-human-study
```

### 🤖 Group 2

```bash
git checkout group2-agents
git pull origin group2-agents

# Work...

git add .
git commit -m "Describe your change"
git push origin group2-agents
```

### 🔀 After PR Merge

```bash
git checkout main
git pull origin main
```

### 🧪 Phase 3

```bash
git checkout main
git pull origin main

git checkout -b joint-analysis
git push origin joint-analysis
```

---

# 🛑 Golden Rules

> **1. Never push directly to `main` for normal feature development.**

> **2. Always `pull` before starting work.**

> **3. Commit small, logical changes.**

> **4. Write meaningful commit messages.**

> **5. Test before pushing.**

> **6. Review the other group's Pull Requests.**

> **7. Never silently modify `LOGGING_SCHEMA.md`.**

> **8. Keep `main` stable at all times.**

> **9. Resolve merge conflicts carefully — don't blindly accept changes.**

> **10. If you're unsure about a Git operation, ask before force-pushing.**

---

## 🌳 Final Branch Lifecycle

```text
                         ┌──────────────────────────┐
                         │           main           │
                         │     Stable Code Only     │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
        ┌─────────────────────┐             ┌─────────────────────┐
        │ group1-human-study  │             │    group2-agents    │
        │                     │             │                     │
        │ Sujal + Utkarsh     │             │ Yashash + Saksham   │
        │                     │             │                     │
        │      Weeks 1–7      │             │      Weeks 1–7      │
        └──────────┬──────────┘             └──────────┬──────────┘
                   │                                   │
                   └──────────────┬────────────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │    joint-analysis   │
                       │                     │
                       │      All 4          │
                       │                     │
                       │      Weeks 8–10     │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │        main         │
                       │   Final Stable Code │
                       └─────────────────────┘
```

