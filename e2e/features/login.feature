Feature: User Login
  As a user
  I want to login to the application
  So that I can access my account and shop for products

  Scenario: Successful login with valid credentials
    Given I navigate to the login page
    When I enter username "spider" and password "Spider@1234"
    And I click the submit button
    Then I should be logged in successfully
    And I should be redirected to the home page
