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
    def __init__(self, report_path="e2e/reports/cucumber-report.json", test_cmd="npm run test:e2e"):
        self.report_path = report_path
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
        logging.info("Starting E2E test execution...")
        result = self.run_command(self.test_cmd)
        
        if result.returncode == 0:
            logging.info("Test suite passed successfully.")
            return True, result.stdout
        else:
            logging.error("Test suite failed.")
            return False, result.stdout

    def parse_failures(self):
        """Parses Cucumber JSON report for failure details."""
        if not os.path.exists(self.report_path):
            logging.warning(f"Report file not found: {self.report_path}")
            return []

        try:
            with open(self.report_path, 'r') as f:
                report = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON report: {e}")
            return []

        failures = []
        for feature in report:
            for scenario in feature.get('elements', []):
                for step in scenario.get('steps', []):
                    if step.get('result', {}).get('status') == 'failed':
                        failure_info = {
                            'feature': feature.get('name', 'Unknown Feature'),
                            'scenario': scenario.get('name', 'Unknown Scenario'),
                            'step': step.get('name', step.get('keyword', 'Hook')),
                            'error': step.get('result', {}).get('error_message'),
                            'location': step.get('match', {}).get('location'),
                            'uri': feature.get('uri')
                        }
                        failures.append(failure_info)
                        logging.info(f"Detected failure in '{failure_info['scenario']}' at step '{failure_info['step']}'")
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
        Analyzes the failures using Gemini 3 Flash.
        Sends ALL failures to the model for better context.
        """
        logging.info(f"Diagnosing {len(failures)} failures...")
        
        failure_summaries = []
        relevant_contents = {}

        for failure in failures:
            summary = f"- Scenario: {failure['scenario']}\n  Step: {failure['step']}\n  Error: {failure['error']}\n  Location: {failure['location']}"
            failure_summaries.append(summary)
            
            # Gather unique file contents
            for path_key in ['location', 'uri']:
                path = failure.get(path_key, "").split(':')[0]
                if path and path not in relevant_contents:
                    relevant_contents[path] = self.get_file_content(path)

        # Always include constants.ts as it's a common source of root causes
        constants_path = "e2e/constants/constants.ts"
        if constants_path not in relevant_contents:
            relevant_contents[constants_path] = self.get_file_content(constants_path)

        context_str = ""
        for path, content in relevant_contents.items():
            context_str += f"\nFILE: {path}\n```\n{content}\n```\n"

        prompt = f"""
        You are an Autonomous QA Engineer. Multiple E2E tests have failed. 
        Your goal is to identify the SINGLE root cause and provide a fix.

        FAILURE LIST:
        {chr(10).join(failure_summaries)}

        CONTEXT FILES:
        {context_str}

        CATEGORIES OF FAILURE:
        - Flaky timing (suggest adding wait)
        - Selectors / Locators (suggest new selector in constants.ts or page object)
        - API contract changes (suggest updating test or app)
        - Assertion mismatch (suggest fixing logic)
        - Application code regressions (suggest fix for app code)

        CRITICAL INSTRUCTIONS:
        1. Look for patterns. If multiple scenarios fail during login or interaction, the root cause is likely a shared selector in constants.ts or a page object.
        2. Do NOT just increase timeouts if a selector looks wrong or an element isn't found.
        3. If you see a mismatch between a selector in constants.ts and the HTML/JSX structure, fix the selector.
        4. The 'target_file' MUST be a valid relative path from the project root.

        REQUIRED OUTPUT (JSON ONLY):
        {{
            "root_cause_category": "one of the categories above",
            "analysis": "detailed reasoning showing you found the root cause",
            "target_file": "relative/path/to/file",
            "old_code": "exact string to replace",
            "new_code": "new string to insert"
        }}
        """

        logging.info("Sending multi-failure context to Gemini 3 Flash...")
        
        try:
            from google import genai
            from google.genai import types
            
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                logging.error("GOOGLE_API_KEY environment variable not set.")
                return None

            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            fix_data = json.loads(response.text)
            logging.info(f"Diagnosis complete: {fix_data.get('root_cause_category')}")
            logging.info(f"Analysis: {fix_data.get('analysis')}")
            return fix_data
            
        except Exception as e:
            logging.error(f"Gemini diagnosis failed: {e}")
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
        self.run_command("git add .")
        self.run_command(f'git commit -m "fix(auto): {message}"')
        # self.run_command("git push") # Uncomment in CI

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

            for attempt in range(self.max_retries):
                logging.info(f"Fix attempt {attempt + 1}/{self.max_retries}")
                failures = self.parse_failures()
                
                if not failures:
                    logging.warning("No failures detected in report. Manual intervention may be needed.")
                    break
                    
                # Process ALL failures for diagnosis
                fix = self.diagnose_failures(failures)
                
                if fix and self.apply_fix(fix):
                    logging.info("Fix applied. Re-running tests to verify...")
                    re_passed, _ = self.run_tests()
                    if re_passed:
                        self.commit_and_push(f"Auto-fixed {len(failures)} test failure(s)")
                        logging.info("Fix verified and committed.")
                        return
                    else:
                        logging.warning("Fix did not resolve the issue. Retrying...")
                else:
                    logging.warning("Could not determine or apply a fix automatically.")
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
