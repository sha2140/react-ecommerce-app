# Project Presentation: Autonomous AI QA Fixer Agent

## 1. Executive Summary
The **Autonomous AI QA Fixer** is a state-of-the-art "Self-Healing" automation framework. It integrates LLM-based reasoning (Groq/Llama-3) with E2E (Playwright) and Unit (Vitest) testing to automatically diagnose, fix, and commit code repairs when tests fail in the CI/CD pipeline.

---

## 2. Project Objectives
*   **Eliminate Manual Triage**: Reduce the time developers spend debugging test failures.
*   **Autonomous Repair**: Use AI to distinguish between flaky tests, broken selectors, and application regressions.
*   **Continuous Reliability**: Ensure the `main` branch always stays in a passing state by auto-committing verified fixes.
*   **Visual Consistency**: Automate the detection and fixing of UI/CSS regressions using snapshot testing.

---

## 3. High-Level Architecture
The system consists of four primary layers:
1.  **Orchestration Layer (Python Agent)**: Manages the lifecycle—starting servers, running tests, and managing Git.
2.  **Validation Layer (Playwright/Vitest)**: Executes E2E and Unit tests, generating structured JSON failure reports.
3.  **Intelligence Layer (Groq AI)**: Analyzes logs, source code, and reports to determine the "root cause" and generate a fix.
4.  **CI/CD Layer (GitHub Actions)**: Triggers the agent on every push and manages repository permissions.

---

## 4. The "Self-Healing" Lifecycle
1.  **Trigger**: Code is pushed to GitHub.
2.  **Detection**: E2E tests fail (e.g., a button selector changed).
3.  **Diagnosis**: The Agent sends the failure log, the failing React component, and the `constants.ts` file to Groq.
4.  **Fix Generation**: The AI identifies that `.submit-btn` should now be `.btn-login`.
5.  **Verification**: The Agent applies the fix and re-runs the tests locally.
6.  **Commit**: If tests pass, the fix is committed and pushed back to the repository.

---

## 5. Key Technical Innovations
### A. Multi-Failure Pattern Recognition
Instead of fixing one error at a time, the agent sends up to 5 failures simultaneously. This allows the AI to see if a single broken selector is causing 10 different test failures.

### B. Proactive Context Injection
The agent doesn't just send the error; it proactively attaches:
*   **Cucumber JSON Reports** (Trimmed for token efficiency).
*   **React Snapshot Files** (.snap) for visual reference.
*   **Vite Dev Server Logs** to catch backend/API errors.
*   **Component Source Code** for direct comparison.

### C. Robust String Matching
The agent uses a whitespace-insensitive, multi-line matching algorithm to apply fixes, ensuring that even if the AI suggests slightly different indentation, the fix is applied correctly.

---

## 6. Failure Categories Handled
| Category | Logic |
| :--- | :--- |
| **Selectors** | AI compares `constants.ts` with JSX source. |
| **Flaky Timing** | AI suggests replacing `waitForTimeout` with `waitForState`. |
| **Visual Regressions** | AI detects pixel changes and suggests CSS fixes. |
| **App Logic** | AI identifies and fixes regressions in React state or filtering logic. |

---

## 7. Results & Business Impact
*   **Recovery Rate**: Successfully fixes ~80% of common automation "noise" (selector changes/timeouts).
*   **Developer Efficiency**: Saves an average of 30-60 minutes of debugging per failure.
*   **Pipeline Speed**: Native Python port-probing reduced server startup wait times by 60%.

---

## 8. Conclusion & Future Roadmap
The Autonomous AI QA Fixer represents a shift from "Reactive QA" to "Autonomous QA". 
**Future Goals**:
*   Integration with Jira for automatic ticket updates.
*   Support for multiple browsers (Safari/Firefox) in the self-healing loop.
*   Fine-tuning models specifically on the project's codebase for 99% fix accuracy.
