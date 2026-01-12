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
        self.git_enabled = True
        self.server_process = None

        # ===== FIX START =====
        self.STEP_DEF_DIRS = ["step-definitions", "/steps/", "\\steps\\"]
        self.FORBIDDEN_EDIT_PATHS = ["step-definitions", "/steps/", "\\steps\\"]
        self.LOCATOR_SOURCE_FILE = "e2e/constants/constants.ts"
        # ===== FIX END =====

    # -------------------- SERVER MANAGEMENT --------------------

    def start_dev_server(self):
        logging.info("Starting development server...")
        server_cmd = "npm run dev -- --host 127.0.0.1 --port 5173"
        log_file = open("dev-server.log", "w")

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

        import socket, time
        start_time = time.time()
        while time.time() - start_time < 120:
            try:
                with socket.create_connection(("127.0.0.1", 5173), timeout=2):
                    logging.info("Dev server is ready.")
                    return True
            except Exception:
                time.sleep(2)

        logging.error("Dev server failed to start.")
        return False

    def stop_dev_server(self):
        if self.server_process:
            logging.info("Stopping dev server...")
            try:
                if os.name == 'nt':
                    subprocess.run(f"taskkill /F /T /PID {self.server_process.pid}", shell=True)
                else:
                    import signal
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            except Exception as e:
                logging.warning(f"Failed to stop server: {e}")

    # -------------------- TEST EXECUTION --------------------

    def run_command(self, cmd):
        logging.info(f"Executing: {cmd}")
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)

    def run_tests(self):
        result = self.run_command(self.test_cmd)
        return result.returncode == 0, result.stdout

    # -------------------- FAILURE PARSING --------------------

    def parse_failures(self):
        failures = []

        if not os.path.exists(self.report_path):
            return failures

        with open(self.report_path, encoding="utf-8") as f:
            report = json.load(f)

        for feature in report:
            for scenario in feature.get("elements", []):
                for step in scenario.get("steps", []):
                    if step.get("result", {}).get("status") == "failed":
                        failures.append({
                            "scenario": scenario.get("name"),
                            "step": step.get("name"),
                            "error": step.get("result", {}).get("error_message"),
                            "location": step.get("match", {}).get("location"),
                            "uri": feature.get("uri")
                        })

        return failures

    # -------------------- DIAGNOSIS --------------------

    def get_file_content(self, path):
        if not path or not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def diagnose_failures(self, failures):
        logging.info(f"Diagnosing {len(failures)} failures...")

        relevant_contents = {}

        for failure in failures[:5]:
            for key in ["location", "uri"]:
                raw_path = failure.get(key)
                if not raw_path:
                    continue

                path = raw_path.split(":")[0].replace("\\", "/")

                # ===== FIX START =====
                # Skip step definition files completely
                if any(d in path for d in self.STEP_DEF_DIRS):
                    logging.info(f"Skipping step definition context: {path}")
                    continue
                # ===== FIX END =====

                if os.path.exists(path) and path not in relevant_contents:
                    relevant_contents[path] = self.get_file_content(path)

        # Always include locator source of truth
        if os.path.exists(self.LOCATOR_SOURCE_FILE):
            relevant_contents[self.LOCATOR_SOURCE_FILE] = self.get_file_content(self.LOCATOR_SOURCE_FILE)

        context_files = ""
        for path, content in relevant_contents.items():
            context_files += f"\nFILE: {path}\n```\n{content[:3000]}\n```\n"

        prompt = f"""
You are an Autonomous QA Engineer.

CRITICAL RULES:
- Step definition files under e2e/step-definitions are READ-ONLY.
- NEVER modify step definition files.
- ALL selector fixes MUST be done in e2e/constants/constants.ts.

FAILURES:
{json.dumps(failures, indent=2)}

CONTEXT:
{context_files}

OUTPUT JSON ONLY:
{{
  "root_cause_category": "Selectors / Locators | Logic | Timing | Snapshot | API",
  "analysis": "why this failed",
  "target_file": "relative/path",
  "old_code": "exact text",
  "new_code": "replacement"
}}
"""

        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        fix = json.loads(response.choices[0].message.content)

        # ===== FIX START =====
        # Force locator fixes into constants.ts
        if fix.get("root_cause_category") == "Selectors / Locators":
            if self.LOCATOR_SOURCE_FILE not in fix.get("target_file", ""):
                logging.warning("Forcing selector fix into constants.ts")
                fix["target_file"] = self.LOCATOR_SOURCE_FILE
        # ===== FIX END =====

        return fix

    # -------------------- APPLY FIX --------------------

    def apply_fix(self, fix):
        file_path = fix.get("target_file", "").replace("\\", "/")

        # ===== FIX START =====
        if any(p in file_path for p in self.FORBIDDEN_EDIT_PATHS):
            logging.error(f"Blocked illegal edit to step definition file: {file_path}")
            return False
        # ===== FIX END =====

        if not os.path.exists(file_path):
            logging.error(f"Target file does not exist: {file_path}")
            return False

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if fix["old_code"] not in content:
            logging.error("Old code not found, aborting fix.")
            return False

        content = content.replace(fix["old_code"], fix["new_code"])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logging.info(f"Fix successfully applied to {file_path}")
        return True

    # -------------------- MAIN LOOP --------------------

    def run(self):
        if not self.start_dev_server():
            sys.exit(1)

        try:
            passed, _ = self.run_tests()
            if passed:
                logging.info("Tests passed. No action needed.")
                return

            failures = self.parse_failures()
            fix = self.diagnose_failures(failures)

            if fix and self.apply_fix(fix):
                passed, _ = self.run_tests()
                if passed:
                    logging.info("Fix verified successfully.")
        finally:
            self.stop_dev_server()


if __name__ == "__main__":
    agent = AIFixerAgent()
    agent.run()
