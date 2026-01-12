import { Given, When, Then } from '@cucumber/cucumber';
import { Page } from 'playwright';
import { LoginPage } from '../pages/LoginPage.js';
import { APP_CONFIG } from '../constants/constants.js';
import * as fs from 'fs';
import * as path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

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

Then('the login page should match the baseline snapshot', async function () {
  const page: Page = this.page;
  const screenshotPath = path.join(process.cwd(), 'e2e', 'reports', 'screenshots', 'current-login.png');
  const baselinePath = path.join(process.cwd(), 'e2e', 'screenshots', 'baseline', 'login-page.png');
  const diffPath = path.join(process.cwd(), 'e2e', 'reports', 'screenshots', 'diff-login.png');

  // Create baseline directory if it doesn't exist
  if (!fs.existsSync(path.dirname(baselinePath))) {
    fs.mkdirSync(path.dirname(baselinePath), { recursive: true });
  }

  // Take current screenshot
  await page.screenshot({ path: screenshotPath });

  // If no baseline exists, save current as baseline and pass (or fail to alert dev)
  if (!fs.existsSync(baselinePath)) {
    fs.copyFileSync(screenshotPath, baselinePath);
    console.log('Baseline snapshot created for login page.');
    return;
  }

  // Compare screenshots
  const img1 = PNG.sync.read(fs.readFileSync(baselinePath));
  const img2 = PNG.sync.read(fs.readFileSync(screenshotPath));
  const { width, height } = img1;
  const diff = new PNG({ width, height });

  const numDiffPixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );

  if (numDiffPixels > 0) {
    fs.writeFileSync(diffPath, PNG.sync.write(diff));
    throw new Error(`Visual regression detected! ${numDiffPixels} pixels changed. Diff saved at ${diffPath}`);
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
