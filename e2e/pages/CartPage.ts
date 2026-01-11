import { Page, Locator } from 'playwright';
import { SELECTORS, APP_CONFIG } from '../constants/constants.js';

/**
 * Cart Page Object Model
 */
export class CartPage {
  readonly page: Page;
  readonly cartContainer: Locator;
  readonly cartItems: Locator;
  readonly emptyCart: Locator;
  readonly cartTotal: Locator;
  readonly clearCartButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.cartContainer = page.locator(SELECTORS.CART.CART_CONTAINER);
    this.cartItems = page.locator(SELECTORS.CART.CART_ITEMS);
    this.emptyCart = page.locator(SELECTORS.CART.EMPTY_CART);
    this.cartTotal = page.locator(SELECTORS.CART.CART_TOTAL);
    this.clearCartButton = page.locator(SELECTORS.CART.CLEAR_CART_BUTTON);
  }

  /**
   * Navigate to cart page using client-side navigation (preserves React state)
   */
  async goto(): Promise<void> {
    // Use client-side navigation by clicking the cart link instead of page.goto()
    // This preserves React Context state (cart items)
    const cartLink = this.page.locator('a.nav-link:has-text("Cart")');
    await cartLink.click();
    await this.page.waitForURL(`${APP_CONFIG.BASE_URL}${APP_CONFIG.CART_URL}`, { timeout: 5000 });
  }

  /**
   * Get cart item by product name
   */
  getCartItemByName(productName: string): Locator {
    return this.page.locator(SELECTORS.CART.CART_ITEMS).filter({
      has: this.page.locator(`text="${productName}"`),
    });
  }

  /**
   * Get cart item names
   */
  async getCartItemNames(): Promise<string[]> {
    const items = this.cartItems;
    const count = await items.count();
    const names: string[] = [];
    
    for (let i = 0; i < count; i++) {
      const item = items.nth(i);
      const name = await item.locator(SELECTORS.CART.CART_ITEM_NAME).textContent();
      if (name) {
        names.push(name.trim());
      }
    }
    
    return names;
  }

  /**
   * Get cart item category by product name
   */
  async getCartItemCategory(productName: string): Promise<string | null> {
    const cartItem = this.getCartItemByName(productName);
    const category = await cartItem.locator(SELECTORS.CART.CART_ITEM_CATEGORY).textContent();
    return category ? category.trim() : null;
  }

  /**
   * Check if cart item exists
   */
  async isCartItemPresent(productName: string): Promise<boolean> {
    const cartItem = this.getCartItemByName(productName);
    return await cartItem.isVisible();
  }

  /**
   * Get cart items count
   */
  async getCartItemsCount(): Promise<number> {
    // Check if cart is empty first
    if (await this.isCartEmpty()) {
      return 0;
    }
    // Wait for cart items to be visible
    await this.cartItems.first().waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
    return await this.cartItems.count();
  }

  /**
   * Check if cart is empty
   */
  async isCartEmpty(): Promise<boolean> {
    return await this.emptyCart.isVisible();
  }

  /**
   * Get cart total
   */
  async getCartTotal(): Promise<string | null> {
    if (await this.isCartEmpty()) {
      return null;
    }
    const totalText = await this.cartTotal.textContent();
    return totalText ? totalText.trim() : null;
  }

  /**
   * Clear cart
   */
  async clearCart(): Promise<void> {
    if (!(await this.isCartEmpty())) {
      await this.clearCartButton.click();
      await this.page.waitForTimeout(300);
    }
  }

  /**
   * Wait for cart page to load
   */
  async waitForPageLoad(): Promise<void> {
    await this.cartContainer.waitFor({ state: 'visible' });
    // Wait for either cart items or empty cart message to appear
    await Promise.race([
      this.cartItems.first().waitFor({ state: 'visible', timeout: 1000 }).catch(() => {}),
      this.emptyCart.waitFor({ state: 'visible', timeout: 1000 }).catch(() => {}),
    ]);
    // Additional wait for React to fully render
    await this.page.waitForTimeout(500);
  }
}
