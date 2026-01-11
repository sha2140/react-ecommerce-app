Feature: Add Products to Cart
  As a user
  I want to add products from different categories to my cart
  So that I can purchase items from various product categories

  Scenario: Add one product from each category to cart
    Given I am logged in to the application
    When I select the "Electronics" category
    And I add "Wireless Headphones" to the cart
    And I select the "Clothing" category
    And I add "Classic T-Shirt" to the cart
    And I select the "Books" category
    And I add "The Great Gatsby" to the cart
    And I select the "Home & Kitchen" category
    And I add "Coffee Maker" to the cart
    When I navigate to the cart page
    Then I should see 4 items in my cart
    And I should see "Wireless Headphones" in my cart
    And I should see "Classic T-Shirt" in my cart
    And I should see "The Great Gatsby" in my cart
    And I should see "Coffee Maker" in my cart
