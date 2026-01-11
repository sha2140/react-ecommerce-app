# Autonomous QA & Code-Fixing Agent

This agent automatically detects E2E test failures, diagnoses the root cause using an LLM, applies fixes to either the test code or the application code, and verifies the fix before committing.

## How it works

1.  **Trigger**: The agent is triggered via GitHub Actions on every push to the repository.
2.  **Test Execution**: It runs the full E2E suite using `npm run test:e2e`.
3.  **Failure Analysis**:
    *   If tests fail, it parses the `e2e/reports/cucumber-report.json`.
    *   It extracts the failed step, the error message, and the relevant code context (feature files and step definitions).
    *   It sends this context to an LLM (e.g., GPT-4o) with instructions to categorize the failure and provide a code fix.
4.  **Auto-Fixing**:
    *   The agent applies the suggested fix using a precise string replacement strategy.
    *   It supports fixes for both test code (selectors, timing, logic) and application code (regressions).
5.  **Verification**:
    *   It re-runs the E2E tests.
    *   If they pass, it commits the changes with a clear message and pushes back to the repository.
    *   If they fail again, it retries once more or exits with an error code to signal a manual review is needed.

## Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini 3 Flash diagnosis.

### Requirements
- Python 3.10+
- Node.js & Playwright
- `google-generativeai` Python library

## Example Commit Messages

- `fix(auto): Fixed timing issue in 'Successful login' by adding await`
- `fix(auto): Updated selector for 'Submit' button in Login.jsx`
- `fix(auto): Resolved assertion mismatch in CartPage.ts`
- `fix(auto): Fixed application regression in ProductList.jsx logic`
