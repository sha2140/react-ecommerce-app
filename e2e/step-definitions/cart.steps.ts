import { Given, When, Then } from '@cucumber/cucumber';
import { Page } from 'playwright';
import { ProductListPage } from '../pages/ProductListPage.js';
import { CartPage } from '../pages/CartPage.js';
import { LoginPage } from '../pages/LoginPage.js';
import { APP_CONFIG, USER_CREDENTIALS } from '../constants/constants.js';

Given('I am logged in to the application', async function () {
  const page: Page = this.page;
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.waitForPageLoad();
  await loginPage.login(USER_CREDENTIALS.SPIDER.username, USER_CREDENTIALS.SPIDER.password);
  // Wait for navigation after successful login
  await page.waitForURL(`${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}`, { timeout: 5000 });
});

When('I select the {string} category', async function (categoryName: string) {
  const productListPage = new ProductListPage(this.page);
  await productListPage.selectCategory(categoryName);
  const isActive = await productListPage.isCategoryActive(categoryName);
  if (!isActive) {
    throw new Error(`Category "${categoryName}" is not active after selection`);
  }
});

When('I add {string} to the cart', async function (productName: string) {
  const productListPage = new ProductListPage(this.page);
  const isDisplayed = await productListPage.isProductDisplayed(productName);
  if (!isDisplayed) {
    throw new Error(`Product "${productName}" is not displayed`);
  }
  await productListPage.addProductToCart(productName);
  // Wait a bit more for cart state to update
  await this.page.waitForTimeout(500);
});

When('I navigate to the cart page', async function () {
  const cartPage = new CartPage(this.page);
  await cartPage.goto();
  await cartPage.waitForPageLoad();
});

Then('I should see {int} items in my cart', async function (expectedCount: number) {
  const cartPage = new CartPage(this.page);
  const actualCount = await cartPage.getCartItemsCount();
  if (actualCount !== expectedCount) {
    throw new Error(`Expected ${expectedCount} items in cart, but found ${actualCount}`);
  }
  await this.page.waitForTimeout(10000);
});

Then('I should see {string} in my cart', async function (productName: string) {
  const cartPage = new CartPage(this.page);
  const isPresent = await cartPage.isCartItemPresent(productName);
  if (!isPresent) {
    const cartItems = await cartPage.getCartItemNames();
    throw new Error(`Product "${productName}" not found in cart. Cart contains: ${cartItems.join(', ')}`);
  }
});