# Autonomous AI QA Fixer - Project Solution Overview

This document summarizes the complete solution developed for the **Autonomous Python QA & Code-Fixing Agent**. It serves as an export of the core logic, prompt engineering, and milestones achieved during the project.

## 1. Project Goal
Build a self-healing CI/CD pipeline that:
- Automatically detects E2E test failures.
- Diagnoses the root cause (Selectors, Timing, App Logic, Visuals).
- Applies precise code fixes.
- Verifies and commits the corrected code autonomously.

---

## 2. Core Prompt Engineering
The following prompt is the "Brain" of the agent, located in `agent/fixer_agent.py`. It uses sophisticated instruction sets to guide the LLM (Groq/Gemini) through diagnosis.

### The System Prompt Logic:
```text
You are an Autonomous QA Engineer. Multiple E2E tests have failed. 
Your goal is to identify the SINGLE root cause and provide a fix.

CRITICAL INSTRUCTIONS:
1. PATTERN RECOGNITION: Look for shared failure points across multiple tests.
2. TIMEOUTS: Treat as masked selector failures, not just timing issues.
3. SOURCE VERIFICATION: Compare test selectors against actual React/JSX source code.
4. VISUAL REGRESSIONS: Detect pixel mismatches and suggest CSS or baseline fixes.
```

---

## 3. Solution Milestones

| Milestone | Feature Added | Benefit |
| :--- | :--- | :--- |
| **01: Orchestration** | `fixer_agent.py` & GitHub Actions | Created the autonomous execution loop. |
| **02: Reliability** | Native Python Port Probing | Eliminated CI hangs and "Connection Refused" errors. |
| **03: Intelligence** | Multi-Failure Diagnosis | Allows AI to see the "Big Picture" and find root causes faster. |
| **04: Visual QA** | Snapshot Testing (`pixelmatch`) | Automatically detects and fixes layout/CSS regressions. |
| **05: Optimization** | Token Trimming & Rate Limiting | Ensures the agent stays within free-tier API quotas. |
| **06: Permissions** | Automated Git Push | Agent handles the full lifecycle from fix to repository update. |

---

## 4. Key Files Created

- **`agent/fixer_agent.py`**: The main Python engine managing the server, tests, and AI calls.
- **`.github/workflows/ai-fixer.yml`**: CI/CD configuration with artifact support and write permissions.
- **`e2e/features/visual.feature`**: New automated visual regression suite.
- **`agent/ARCHITECTURE.md`**: Technical design and mermaid execution diagrams.
- **`agent/requirements.txt`**: Minimal dependency set (`groq`, `pngjs`, `pixelmatch`).

---

## 5. How to Run the Solution

### Prerequisites:
- A Groq API Key (saved as `GROQ_API_KEY` in GitHub Secrets).

### Local Execution:
```bash
# 1. Install dependencies
npm install
pip install -r agent/requirements.txt

# 2. Run the agent (will start server and tests)
$env:GROQ_API_KEY="your_key"
python agent/fixer_agent.py
```

### Automated Flow:
Simply push code to `main`. If any test fails, the agent will:
1. Upload the failure report as a GitHub artifact.
2. Start a self-healing cycle.
3. Push a `fix(auto): ...` commit if it successfully repairs the code.

---

## 6. Project Solution Status
**Status**: Production Ready ✅
**Capabilities**: Functional Repair, Visual Repair, Self-Correction, Automated Deployment.
