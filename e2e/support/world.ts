import { setWorldConstructor, setDefaultTimeout, World, IWorldOptions } from '@cucumber/cucumber';
import { Page, Browser, BrowserContext } from 'playwright';
import { LoginPage } from '../pages/LoginPage.js';
import { ProductListPage } from '../pages/ProductListPage.js';
import { CartPage } from '../pages/CartPage.js';

// Set default timeout to 30 seconds
setDefaultTimeout(30 * 1000);

export interface CucumberWorld extends World {
  page: Page;
  browser: Browser;
  context: BrowserContext;
  loginPage: LoginPage;
  productListPage: ProductListPage;
  cartPage: CartPage;
  scenarioName: string;
  attachments: Array<{ data: string; media: { type: string } }>;
}

export class CustomWorld extends World implements CucumberWorld {
  page!: Page;
  browser!: Browser;
  context!: BrowserContext;
  loginPage!: LoginPage;
  productListPage!: ProductListPage;
  cartPage!: CartPage;
  scenarioName: string = '';
  attachments: Array<{ data: string; media: { type: string } }> = [];

  constructor(options: IWorldOptions) {
    super(options);
  }
}

setWorldConstructor(CustomWorld);
