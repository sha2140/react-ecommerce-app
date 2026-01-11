# React E-Commerce Application

A modern, responsive React e-commerce application with shopping cart functionality, product categories, and a beautiful UI.

## Features

- 🛍️ **Product Categories**: Browse products by category (Electronics, Clothing, Books, Home & Kitchen)
- 🛒 **Shopping Cart**: Add items to cart, update quantities, and remove items
- 🎨 **Modern UI**: Clean, responsive design with smooth animations
- 🔍 **Category Filtering**: Filter products by category
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Getting Started

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

## Project Structure

```
src/
  ├── components/
  │   ├── Header.jsx       # Navigation header with cart badge
  │   ├── ProductList.jsx  # Product listing with category filters
  │   ├── ProductCard.jsx  # Individual product card component
  │   └── Cart.jsx         # Shopping cart page
  ├── context/
  │   └── CartContext.jsx  # Cart state management
  ├── data/
  │   └── products.js      # Product data and categories
  ├── App.jsx              # Main app component with routing
  ├── App.css              # Global styles
  └── main.jsx             # Entry point
```

## Technologies Used

- React 18
- React Router DOM
- Vite
- Context API for state management

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Features in Detail

### Product Categories
- All Products
- Electronics
- Clothing
- Books
- Home & Kitchen

### Cart Functionality
- Add products to cart
- Update item quantities
- Remove items from cart
- View cart total
- Clear entire cart

Enjoy shopping! 🎉
