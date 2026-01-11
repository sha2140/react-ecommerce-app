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

    def diagnose_failure(self, failure):
        """
        Analyzes the failure using Gemini 3 Flash.
        """
        logging.info(f"Diagnosing failure: {failure['scenario']} -> {failure['step']}")
        
        # Gather context for diagnosis
        step_def_content = self.get_file_content(failure['location'])
        feature_content = self.get_file_content(failure['uri'])
        
        prompt = f"""
        You are an Autonomous QA Engineer. An E2E test failed. 
        Your goal is to identify the root cause and provide a fix.

        FAILURE DETAILS:
        Feature: {failure['feature']}
        Scenario: {failure['scenario']}
        Failed Step: {failure['step']}
        Error: {failure['error']}

        CONTEXT:
        Feature File Content:
        {feature_content}

        Step Definition Content:
        {step_def_content}

        CATEGORIES OF FAILURE:
        - Flaky timing (suggest adding wait)
        - Selectors / Locators (suggest new selector)
        - API contract changes (suggest updating test or app)
        - Assertion mismatch (suggest fixing logic)
        - Application code regressions (suggest fix for app code)

        POLICY:
        - Prefer fixing tests ONLY if the application behavior is correct.
        - If the application is broken, fix the application code.
        - Never disable assertions; fix them.
        - Keep changes minimal and safe.

        REQUIRED OUTPUT (JSON ONLY):
        {{
            "root_cause_category": "one of the categories above",
            "analysis": "detailed reasoning",
            "target_file": "relative/path/to/file",
            "old_code": "exact string to replace",
            "new_code": "new string to insert"
        }}
        """

        logging.info("Sending context to Gemini 3 Flash for diagnosis...")
        
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
                
            # Process the first failure (can be extended to handle multiple)
            failure = failures[0]
            fix = self.diagnose_failure(failure)
            
            if fix and self.apply_fix(fix):
                logging.info("Fix applied. Re-running tests to verify...")
                re_passed, _ = self.run_tests()
                if re_passed:
                    self.commit_and_push(f"Auto-fixed test failure in {failure['scenario']}")
                    logging.info("Fix verified and committed.")
                    return
                else:
                    logging.warning("Fix did not resolve the issue. Retrying...")
            else:
                logging.warning("Could not determine or apply a fix automatically.")
                break
        
        logging.error("Autonomous fixing failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous QA & Code-Fixing Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run without applying fixes or committing")
    args = parser.parse_args()
    
    agent = AIFixerAgent()
    if args.dry_run:
        agent.git_enabled = False
        
    agent.run()
