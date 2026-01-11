import { Page, Locator } from 'playwright';
import { SELECTORS, APP_CONFIG } from '../constants/constants.js';

/**
 * Product List Page Object Model
 */
export class ProductListPage {
  readonly page: Page;
  readonly categoryButtons: Locator;
  readonly productsGrid: Locator;
  readonly productCards: Locator;

  constructor(page: Page) {
    this.page = page;
    this.categoryButtons = page.locator(SELECTORS.PRODUCTS.CATEGORY_BUTTON);
    this.productsGrid = page.locator(SELECTORS.PRODUCTS.PRODUCTS_GRID);
    this.productCards = page.locator(SELECTORS.PRODUCTS.PRODUCT_CARD);
  }

  /**
   * Navigate to product list page (home page)
   */
  async goto(): Promise<void> {
    await this.page.goto(`${APP_CONFIG.BASE_URL}${APP_CONFIG.HOME_URL}`);
  }

  /**
   * Select a category filter
   */
  async selectCategory(categoryName: string): Promise<void> {
    const categoryButton = this.page.locator(`.category-btn:has-text("${categoryName}")`);
    await categoryButton.click();
    // Wait for products to load/filter
    await this.page.waitForTimeout(500);
  }

  /**
   * Get product card by product name
   */
  getProductCardByName(productName: string): Locator {
    return this.page.locator(SELECTORS.PRODUCTS.PRODUCT_CARD).filter({
      hasText: productName,
    });
  }

  /**
   * Add product to cart by product name
   */
  async addProductToCart(productName: string): Promise<void> {
    const productCard = this.getProductCardByName(productName);
    const addToCartButton = productCard.locator(SELECTORS.PRODUCTS.ADD_TO_CART_BUTTON);
    await addToCartButton.click();
    // Wait for cart to update
    await this.page.waitForTimeout(300);
  }

  /**
   * Check if product is displayed
   */
  async isProductDisplayed(productName: string): Promise<boolean> {
    const productCard = this.getProductCardByName(productName);
    return await productCard.isVisible();
  }

  /**
   * Get all visible product names
   */
  async getVisibleProductNames(): Promise<string[]> {
    const productCards = this.productCards;
    const count = await productCards.count();
    const names: string[] = [];
    
    for (let i = 0; i < count; i++) {
      const productCard = productCards.nth(i);
      const name = await productCard.locator(SELECTORS.PRODUCTS.PRODUCT_NAME).textContent();
      if (name) {
        names.push(name.trim());
      }
    }
    
    return names;
  }

  /**
   * Check if category is active
   */
  async isCategoryActive(categoryName: string): Promise<boolean> {
    const categoryButton = this.page.locator(`.category-btn:has-text("${categoryName}")`);
    const className = await categoryButton.getAttribute('class');
    return className?.includes('active') || false;
  }
}
