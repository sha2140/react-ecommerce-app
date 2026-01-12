Feature: Visual Regression Testing
  As a developer
  I want to ensure the UI looks consistent
  So that I can catch visual regressions automatically

  Scenario: Verify login page visual appearance
    Given I navigate to the login page
    Then the login page should match the baseline snapshot
