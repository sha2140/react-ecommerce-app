import { Page, Locator } from 'playwright';
import { SELECTORS, APP_CONFIG } from '../constants/constants.js';

/**
 * Login Page Object Model
 */
export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly loginContainer: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator(SELECTORS.LOGIN.USERNAME_INPUT);
    this.passwordInput = page.locator(SELECTORS.LOGIN.PASSWORD_INPUT);
    this.submitButton = page.locator(SELECTORS.LOGIN.SUBMIT_BUTTON);
    this.errorMessage = page.locator(SELECTORS.LOGIN.ERROR_MESSAGE);
    this.loginContainer = page.locator(SELECTORS.LOGIN.LOGIN_CONTAINER);
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.page.goto(`${APP_CONFIG.BASE_URL}${APP_CONFIG.LOGIN_URL}`);
  }

  /**
   * Enter username
   */
  async enterUsername(username: string): Promise<void> {
    await this.usernameInput.fill(username);
  }

  /**
   * Enter password
   */
  async enterPassword(password: string): Promise<void> {
    await this.passwordInput.fill(password);
  }

  /**
   * Click submit button
   */
  async clickSubmit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Login with credentials
   */
  async login(username: string, password: string): Promise<void> {
    await this.enterUsername(username);
    await this.enterPassword(password);
    await this.clickSubmit();
  }

  /**
   * Check if error message is visible
   */
  async isErrorMessageVisible(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent() || '';
  }

  /**
   * Wait for login page to load
   */
  async waitForPageLoad(): Promise<void> {
    await this.loginContainer.waitFor({ state: 'visible' });
  }

  /**
   * Check if login page is displayed
   */
  async isLoginPageDisplayed(): Promise<boolean> {
    return await this.loginContainer.isVisible();
  }
}
