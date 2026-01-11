module.exports = {
  default: {
    import: [
      'e2e/step-definitions/**/*.ts',
      'e2e/hooks/**/*.ts',
      'e2e/support/**/*.ts'
    ],
    format: [
      'progress-bar',
      'json:e2e/reports/cucumber-report.json',
      'usage:e2e/reports/usage.txt'
    ],
    paths: ['e2e/features/**/*.feature'],
    publishQuiet: true,
  }
};
