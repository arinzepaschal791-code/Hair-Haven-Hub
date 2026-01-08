# GlowHair Nigeria - Premium E-commerce

## Overview
GlowHair Nigeria is a premium e-commerce website for selling wigs, bone straight hair, and hair care products. Built for Nigerian customers with luxury design, flexible payment options, and WhatsApp integration.

## Key Features
- **Product Catalog**: Bone straight hair, wigs, and hair care products
- **2-Installment Payment**: 50% upfront, 50% within 30 days
- **Nigerian Checkout**: States and LGAs selection for Lagos and FCT
- **Admin Dashboard**: Manual product import and order management
- **Marketing**: WhatsApp FAB, social proof popups, testimonials, newsletter

## Tech Stack
- **Frontend**: React, TanStack Query, Wouter, Tailwind CSS, shadcn/ui
- **Backend**: Express.js with in-memory storage
- **Styling**: Playfair Display (headings) + Inter (body) fonts

## Project Structure
```
client/src/
├── components/
│   ├── admin/          # ProductForm for admin
│   ├── cart/           # CartItem, CartSummary
│   ├── checkout/       # CheckoutSteps, DeliveryForm, PaymentOptions
│   ├── home/           # Hero, Collections, Testimonials, Newsletter
│   ├── layout/         # Header, Footer, PromoBar, WhatsAppFAB
│   └── product/        # ProductCard, ProductGrid, FilterSidebar
├── lib/
│   ├── cart.tsx        # Cart context (localStorage)
│   ├── theme.tsx       # Dark/light mode toggle
│   └── queryClient.ts  # TanStack Query setup
├── pages/
│   ├── Home.tsx        # Landing page
│   ├── Shop.tsx        # Product listing with filters
│   ├── ProductDetail.tsx
│   ├── Cart.tsx
│   ├── Checkout.tsx    # Multi-step checkout
│   ├── Admin.tsx       # Dashboard with product management
│   └── About.tsx

server/
├── routes.ts           # API endpoints
├── storage.ts          # MemStorage with seeded products
└── index.ts            # Express server

shared/
└── schema.ts           # Drizzle schema, types, Nigerian states/LGAs
```

## API Endpoints
- `GET /api/products` - List all products
- `GET /api/products/:id` - Get single product
- `POST /api/products` - Create product (admin)
- `DELETE /api/products/:id` - Delete product (admin)
- `GET /api/orders` - List all orders (admin)
- `POST /api/orders` - Create order
- `GET /api/testimonials` - List testimonials
- `POST /api/subscribe` - Newsletter subscription
- `GET /api/meta/states` - Nigerian states
- `GET /api/meta/lgas?state=Lagos` - LGAs for state

## Development
```bash
npm run dev   # Starts Express + Vite on port 5000
```

## User Preferences
- Premium luxury aesthetic with gold accents
- Nigerian Naira (NGN) currency formatting
- WhatsApp as primary customer support channel
- Mobile-first responsive design

## Recent Changes
- January 2026: Initial implementation with full e-commerce flow
  - Multi-step checkout with installment payment
  - Admin product import functionality
  - Nigerian states/LGAs selection
  - Social proof and marketing features
