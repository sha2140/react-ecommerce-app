const reporter = require('cucumber-html-reporter');
const path = require('path');
const fs = require('fs');

const reportsDir = path.join(__dirname, 'reports');
const jsonReportPath = path.join(reportsDir, 'cucumber-report.json');

if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir, { recursive: true });
}

const options = {
  theme: 'bootstrap',
  jsonFile: jsonReportPath,
  output: path.join(reportsDir, 'cucumber-report.html'),
  reportSuiteAsScenarios: true,
  scenarioTimestamp: true,
  launchReport: false,
  metadata: {
    'App Version': '1.0.0',
    'Test Environment': 'Development',
    Browser: 'Chromium',
    Platform: 'Windows',
    Parallel: 'Scenarios',
    Executed: 'Remote',
  },
  screenshotsDirectory: path.join(reportsDir, 'screenshots'),
  storeScreenshots: true,
  screenshotsOnlyOnFailure: true,
  ignoreBadJsonFile: true,
};

reporter.generate(options);
