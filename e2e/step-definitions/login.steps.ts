import { Given, When, Then } from '@cucumber/cucumber';
import { Page } from 'playwright';
import { LoginPage } from '../pages/LoginPage.js';
import { APP_CONFIG } from '../constants/constants.js';

Given('I navigate to the login page', async function () {
  const loginPage: LoginPage = this.loginPage;
  const page: Page = this.page;
  await loginPage.goto();
  await loginPage.waitForPageLoad();
  const isDisplayed = await loginPage.isLoginPageDisplayed();
  if (!isDisplayed) {
    throw new Error('Login page is not displayed');
  }
});

When('I enter username {string} and password {string}', async function (username: string, password: string) {
  const loginPage: LoginPage = this.loginPage;
  await loginPage.enterUsername(username);
  await loginPage.enterPassword(password);
});

When('I click the submit button', async function () {
  const loginPage: LoginPage = this.loginPage;
  await loginPage.clickSubmit();
});

Then('I should be logged in successfully', async function () {
  const page: Page = this.page;
  // Wait for navigation after successful login
  await page.waitForURL(`${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}`, { timeout: 5000 });
  const currentUrl = page.url();
  if (currentUrl !== `${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}`) {
    throw new Error(`Expected URL to be ${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}, but got ${currentUrl}`);
  }
});

Then('I should be redirected to the home page', async function () {
  const page: Page = this.page;
  const currentUrl = page.url();
  if (currentUrl !== `${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}`) {
    throw new Error(`Expected URL to be ${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}, but got ${currentUrl}`);
  }
  await page.waitForTimeout(10000)
});
