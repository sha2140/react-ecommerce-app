/**
 * Application Constants
 */
export const APP_CONFIG = {
  BASE_URL: process.env.BASE_URL || 'http://localhost:5173',
  LOGIN_URL: '/login',
  HOME_URL: '/',
  CART_URL: '/cart',
};

/**
 * User Credentials
 */
export const USER_CREDENTIALS = {
  SPIDER: {
    username: 'spider',
    password: 'Spider@1234',
  },
};

/**
 * Selectors
 */
export const SELECTORS = {
  LOGIN: {
    USERNAME_INPUT: '#username',
    PASSWORD_INPUT: '#password',
    SUBMIT_BUTTON: '.submit-btn',
    ERROR_MESSAGE: '.error-message',
    LOGIN_CONTAINER: '.login-container',
  },
  PRODUCTS: {
    PRODUCT_CARD: '.product-card',
    PRODUCT_NAME: '.product-name',
    PRODUCT_CATEGORY: '.product-category',
    ADD_TO_CART_BUTTON: '.btn-primary-1234',
    CATEGORY_BUTTON: '.category-btn',
    CATEGORY_ACTIVE: '.category-btn.active',
    PRODUCTS_GRID: '.products-grid',
  },
  CART: {
    CART_CONTAINER: '.cart-container',
    CART_ITEMS: '.cart-item',
    CART_ITEM_NAME: '.cart-item-info h3',
    CART_ITEM_CATEGORY: '.cart-item-category',
    EMPTY_CART: '.empty-cart',
    CART_TOTAL: '.cart-total h3',
    CLEAR_CART_BUTTON: '.btn-secondary',
  },
};

/**
 * Product Names for Testing
 */
export const PRODUCTS = {
  ELECTRONICS: 'Wireless Headphones',
  CLOTHING: 'Classic T-Shirt',
  BOOKS: 'The Great Gatsby',
  HOME_KITCHEN: 'Coffee Maker',
};
