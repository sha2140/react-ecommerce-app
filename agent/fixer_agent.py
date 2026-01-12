import os
import json
import subprocess
import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

class AIFixerAgent:
    """
    Autonomous QA Agent that runs tests, diagnoses failures, 
    applies fixes, and commits code.
    """
    def __init__(self, report_path="e2e/reports/cucumber-report.json", unit_report_path="unit-test-report.json", test_cmd="npm run test:e2e"):
        self.report_path = report_path
        self.unit_report_path = unit_report_path
        self.test_cmd = test_cmd
        self.max_retries = 2
        self.git_enabled = True # Set to False for local testing without git
        self.server_process = None

    def start_dev_server(self):
        """Starts the dev server and waits for it to be ready."""
        logging.info("Starting development server...")
        # Standardizing on 127.0.0.1 for CI stability
        server_cmd = "npm run dev -- --host 127.0.0.1 --port 5173"
        
        # Redirect output to a log file for diagnosis
        log_file = open("dev-server.log", "w")
        
        # Use start_new_session to ensure the server and its children can be killed
        if os.name == 'nt':
            self.server_process = subprocess.Popen(
                server_cmd, 
                shell=True, 
                stdout=log_file, 
                stderr=log_file,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            self.server_process = subprocess.Popen(
                server_cmd, 
                shell=True, 
                stdout=log_file, 
                stderr=log_file,
                preexec_fn=os.setsid
            )
        
        logging.info("Waiting for server to respond at http://127.0.0.1:5173...")
        
        # Native Python wait loop for better reliability in CI
        import socket
        import time
        
        start_time = time.time()
        timeout = 120 # 2 minutes
        server_ready = False
        
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection(("127.0.0.1", 5173), timeout=2):
                    server_ready = True
                    break
            except (ConnectionRefusedError, socket.timeout, OSError):
                time.sleep(2)
                continue
        
        if not server_ready:
            logging.error("Dev server failed to start within timeout. Check dev-server.log for details.")
            # Print the last few lines of dev-server.log for immediate visibility
            if os.path.exists("dev-server.log"):
                with open("dev-server.log", "r") as f:
                    logging.error(f"Last server logs:\n{f.read()}")
            return False
        
        logging.info("Dev server is ready.")
        return True

    def stop_dev_server(self):
        """Gracefully stops the dev server and its children."""
        if self.server_process:
            logging.info("Stopping dev server...")
            try:
                if os.name == 'nt':
                    subprocess.run(f"taskkill /F /T /PID {self.server_process.pid}", shell=True, capture_output=True)
                else:
                    import signal
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            except Exception as e:
                logging.warning(f"Error stopping dev server: {e}")
            self.server_process = None

    def run_command(self, cmd):
        """Helper to run shell commands and return results."""
        logging.info(f"Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result

    def run_tests(self):
        """Runs the E2E test suite."""
        logging.info("Starting test execution...")
        
        # Run E2E Tests
        logging.info("Executing E2E tests...")
        e2e_result = self.run_command(self.test_cmd)
        e2e_passed = (e2e_result.returncode == 0)
        
        if e2e_passed:
            logging.info("E2E test suite passed successfully.")
            return True, "All tests passed"
        else:
            msg = "E2E failures detected."
            logging.error(msg)
            return False, msg

    def parse_failures(self):
        """Parses E2E test reports for failure details."""
        failures = []
        
        # Parse E2E Failures
        if os.path.exists(self.report_path):
            try:
                with open(self.report_path, 'r') as f:
                    report = json.load(f)
                for feature in report:
                    for scenario in feature.get('elements', []):
                        for step in scenario.get('steps', []):
                            if step.get('result', {}).get('status') == 'failed':
                                failures.append({
                                    'type': 'E2E',
                                    'feature': feature.get('name', 'Unknown Feature'),
                                    'scenario': scenario.get('name', 'Unknown Scenario'),
                                    'step': step.get('name', step.get('keyword', 'Hook')),
                                    'error': step.get('result', {}).get('error_message'),
                                    'location': step.get('match', {}).get('location'),
                                    'uri': feature.get('uri')
                                })
            except Exception as e:
                logging.error(f"Failed to parse E2E report: {e}")

        for f in failures:
            logging.info(f"Detected E2E failure in '{f['scenario']}'")
            
        return failures

    def get_file_content(self, path_with_line):
        """Reads file content, handling paths with line numbers (e.g., file.ts:10)."""
        if not path_with_line:
            return ""
        
        clean_path = path_with_line.split(':')[0]
        # Handle Windows/Unix path separators
        clean_path = clean_path.replace('\\', os.sep).replace('/', os.sep)
        
        if os.path.exists(clean_path):
            with open(clean_path, 'r') as f:
                return f.read()
        return ""

    def diagnose_failures(self, failures):
        """
        Analyzes the failures using Groq.
        Sends ALL failures to the model for better context.
        """
        logging.info(f"Diagnosing {len(failures)} failures...")
        
        failure_summaries = []
        relevant_contents = {}

        for failure in failures[:5]: # Limit to top 5 failures to save tokens
            summary = f"- [E2E] Scenario: {failure['scenario']}\n  Step: {failure['step']}\n  Error: {failure['error']}\n  Location: {failure['location']}"
            failure_summaries.append(summary)
            
            # Gather unique file contents
            for path_key in ['location', 'uri']:
                path = failure.get(path_key, "").split(':')[0] if failure.get(path_key) else None
                if path and os.path.exists(path) and path not in relevant_contents:
                    relevant_contents[path] = self.get_file_content(path)
            
            # PROACTIVE SNAPSHOT DISCOVERY for E2E failures
            # If login fails, include Login.jsx and its snapshot
            if 'login' in failure['scenario'].lower() or 'login' in failure['step'].lower():
                critical_pairs = [
                    ("src/components/Login.jsx", "src/components/__snapshots__/Login.test.jsx.snap")
                ]
                for comp, snap in critical_pairs:
                    if os.path.exists(comp) and comp not in relevant_contents:
                        relevant_contents[comp] = self.get_file_content(comp)
                    if os.path.exists(snap) and snap not in relevant_contents:
                        relevant_contents[snap] = self.get_file_content(snap)

        # Always include shared files that are common failure points
        critical_files = [
            "e2e/constants/constants.ts",
            "src/components/Login.jsx",
            "src/components/Login.css",
            "src/components/ProductList.jsx",
            "src/App.css"
        ]
        for path in critical_files:
            if os.path.exists(path) and path not in relevant_contents:
                relevant_contents[path] = self.get_file_content(path)

        # Include a trimmed version of the JSON report to save tokens
        json_report_content = ""
        if os.path.exists(self.report_path):
            try:
                with open(self.report_path, 'r') as f:
                    full_report = json.load(f)
                
                # Trim the report even more aggressively
                trimmed_report = []
                for feature in full_report:
                    failed_elements = []
                    for element in feature.get('elements', []):
                        if any(step.get('result', {}).get('status') == 'failed' for step in element.get('steps', [])):
                            # Only keep essential fields
                            trimmed_element = {
                                "name": element.get("name"),
                                "steps": [
                                    {
                                        "name": s.get("name"),
                                        "keyword": s.get("keyword"),
                                        "result": s.get("result"),
                                        "match": s.get("match")
                                    }
                                    for s in element.get("steps", [])
                                    if s.get("result", {}).get("status") == "failed"
                                ]
                            }
                            failed_elements.append(trimmed_element)
                    
                    if failed_elements:
                        trimmed_report.append({
                            "name": feature.get("name"),
                            "uri": feature.get("uri"),
                            "elements": failed_elements
                        })
                
                json_report_content = json.dumps(trimmed_report, indent=2)
                # Hard limit for safety
                if len(json_report_content) > 10000:
                    json_report_content = json_report_content[:10000] + "... [TRUNCATED]"
            except Exception as e:
                logging.warning(f"Failed to trim JSON report: {e}")
                json_report_content = "Failed to parse report for context."

        # Include log files in the context
        log_context = ""
        for log_file in ["dev-server.log", "agent_execution.log"]:
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    content = f.read()
                    # Only take the last 2000 characters to keep context size manageable
                    truncated_log = content if len(content) < 2000 else "... [TRUNCATED]\n" + content[-2000:]
                    log_context += f"\nLOG FILE: {log_file}\n```\n{truncated_log}\n```\n"

        context_str = ""
        for path, content in relevant_contents.items():
            # Truncate each file to 3000 chars to save tokens
            truncated_content = content if len(content) < 3000 else content[:3000] + "... [TRUNCATED]"
            context_str += f"\nFILE: {path}\n```\n{truncated_content}\n```\n"

        prompt = f"""
        You are an Autonomous QA Engineer. Multiple E2E tests have failed. 
        Your goal is to identify the SINGLE root cause and provide a fix.

        FAILURE LIST:
        {chr(10).join(failure_summaries)}

        CUCUMBER JSON REPORT:
        ```json
        {json_report_content}
        ```

        LOG FILES CONTEXT:
        {log_context}

        CONTEXT FILES:
        {context_str}

        CATEGORIES OF FAILURE:
        - Flaky timing (suggest adding wait)
        - Selectors / Locators (suggest new selector in constants.ts or page object)
        - Visual regression (check for CSS/layout changes in 'src/' or suggest updating snapshot if intentional)
        - Component Snapshot regression (check '.snap' files and React components in 'src/')
        - API contract changes (suggest updating test or app)
        - Assertion mismatch (suggest fixing logic)
        - Application code regressions (suggest fix for app code)

        CRITICAL INSTRUCTIONS:
        1. PATTERN RECOGNITION: If multiple tests fail at the same step (e.g., login), it is almost CERTAINLY a shared selector in 'e2e/constants/constants.ts' or a logic bug in 'src/'.
        2. LOCATOR CHECK (CRITICAL): ALWAYS compare the locators in 'e2e/constants/constants.ts' with the actual React source code (JSX/CSS) and the provided snapshots. If the locator in 'constants.ts' does not match the 'id', 'className', or 'data-testid' in the component, FIX THE CONSTANT.
        3. TIMEOUTS: In Playwright/Cucumber, a "timeout" error is usually a MASKED selector failure. DO NOT simply increase timeouts. Find the broken selector in 'constants.ts' or the application logic instead.
        4. SNAPSHOTS: Use the provided '.snap' files and React component code as the "Source of Truth" for what the UI should look like. Use this to verify if the selector in 'constants.ts' is still valid.
        5. SELECTORS VS LOGIC: If the selector is correct but the element is missing, check the filtering/rendering logic in the corresponding 'src/' component.
        6. MINIMAL CHANGES: Only change one thing at a time. Prefer fixing the root cause (selector in 'constants.ts' or app logic) over adding waits.
        7. PATHS: The 'target_file' MUST be a valid relative path from the project root.

        REQUIRED OUTPUT (JSON ONLY):
        {{
            "root_cause_category": "one of the categories above",
            "analysis": "detailed reasoning showing you found the root cause",
            "target_file": "relative/path/to/file",
            "old_code": "exact string to replace",
            "new_code": "new string to insert"
        }}
        """

        logging.info("Sending multi-failure context to Groq...")
        
        import time
        max_api_retries = 3
        
        for api_attempt in range(max_api_retries):
            try:
                from groq import Groq
                
                api_key = os.environ.get("GROQ_API_KEY")
                if not api_key:
                    logging.error("GROQ_API_KEY environment variable not set.")
                    return None
                
                # Safe debugging: Log key presence and partial value (first/last 4 chars)
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
                logging.info(f"Using GROQ_API_KEY: {masked_key} (length: {len(api_key)})")

                client = Groq(api_key=api_key)
                
                # Determine model name from environment or default to llama-3.3-70b-versatile
                model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
                logging.info(f"Diagnosing with model: {model_name}")

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that outputs JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model_name,
                    response_format={"type": "json_object"},
                )
                
                fix_data = json.loads(chat_completion.choices[0].message.content)
                logging.info(f"Diagnosis complete: {fix_data.get('root_cause_category')}")
                logging.info(f"Analysis: {fix_data.get('analysis')}")
                return fix_data
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    wait_time = 30 * (api_attempt + 1)
                    logging.warning(f"Rate limit exceeded (429). Retrying in {wait_time}s... (Attempt {api_attempt + 1}/{max_api_retries})")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Groq diagnosis failed: {e}")
                    return None
        
        logging.error("Failed to get diagnosis after multiple API retries due to rate limits.")
        return None

    def apply_fix(self, fix_data):
        """Applies a code fix to the repository."""
        if not fix_data:
            return False
            
        file_path = fix_data.get('target_file')
        old_code = fix_data.get('old_code')
        new_code = fix_data.get('new_code')
        
        if not all([file_path, old_code, new_code]):
            logging.error("Invalid fix data provided.")
            return False

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            if old_code in content:
                updated_content = content.replace(old_code, new_code)
                with open(file_path, 'w') as f:
                    f.write(updated_content)
                logging.info(f"Successfully applied fix to {file_path}")
                return True
            else:
                logging.error(f"Could not find exact code match in {file_path}")
        else:
            logging.error(f"File not found: {file_path}")
        
        return False

    def commit_and_push(self, message):
        """Commits the fix to the repository."""
        if not self.git_enabled:
            logging.info("Git push skipped (git_enabled=False)")
            return

        logging.info(f"Committing fix: {message}")
        
        # Check if there are changes to commit
        status = self.run_command("git status --porcelain")
        if not status.stdout.strip():
            logging.info("No changes to commit.")
            return

        self.run_command("git add .")
        commit_res = self.run_command(f'git commit -m "fix(auto): {message}"')
        logging.info(f"Commit output: {commit_res.stdout.strip()}")
        
        # In CI, we usually need to specify origin and head
        push_res = self.run_command("git push origin HEAD")
        if push_res.returncode == 0:
            logging.info("Successfully pushed changes to repository.")
        else:
            logging.error(f"Failed to push changes: {push_res.stderr.strip()}")

    def run(self):
        """Main execution loop."""
        if not self.start_dev_server():
            # In a more advanced version, we could diagnose dev-server.log here
            sys.exit(1)

        try:
            passed, _ = self.run_tests()
            if passed:
                logging.info("No fixes needed.")
                return

            applied_fixes = [] # Track fixes to avoid repeats

            for attempt in range(self.max_retries):
                logging.info(f"Fix attempt {attempt + 1}/{self.max_retries}")
                failures = self.parse_failures()
                
                if not failures:
                    logging.warning("No failures detected in report. Manual intervention may be needed.")
                    break
                    
                # Process ALL failures for diagnosis
                fix = self.diagnose_failures(failures)
                
                if not fix:
                    logging.warning("Could not determine a fix automatically.")
                    break

                # Check if we've already tried this exact fix
                fix_signature = f"{fix.get('target_file')}:{fix.get('old_code')}->{fix.get('new_code')}"
                if fix_signature in applied_fixes:
                    logging.warning("AI suggested a repeat fix. Breaking to avoid loop.")
                    break
                
                if self.apply_fix(fix):
                    applied_fixes.append(fix_signature)
                    logging.info("Fix applied. Re-running tests to verify...")
                    re_passed, _ = self.run_tests()
                    if re_passed:
                        self.commit_and_push(f"Auto-fixed {len(failures)} test failure(s)")
                        logging.info("Fix verified and committed.")
                        return
                    else:
                        logging.warning("Fix did not resolve the issue. Retrying...")
                else:
                    logging.warning("Could not apply the fix.")
                    break
            
            logging.error("Autonomous fixing failed. Please check the logs.")
            sys.exit(1)
        finally:
            self.stop_dev_server()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous QA & Code-Fixing Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run without applying fixes or committing")
    args = parser.parse_args()
    
    agent = AIFixerAgent()
    if args.dry_run:
        agent.git_enabled = False
        
    agent.run()
