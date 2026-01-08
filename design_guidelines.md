# Design Guidelines: Premium Hair Products E-Commerce

## Design Approach
**Reference-Based: Luxury E-Commerce + Beauty Industry Standards**
Drawing inspiration from Shopify, Glossier, and premium African beauty brands. Focus on visual storytelling, trust-building, and conversion optimization for the Nigerian market.

## Typography System
- **Primary Font**: Playfair Display (headings) - elegant, premium feel
- **Secondary Font**: Inter (body, UI) - clean readability
- **Hierarchy**:
  - Hero Headlines: text-5xl to text-7xl, font-bold
  - Section Headers: text-3xl to text-4xl, font-semibold
  - Product Titles: text-xl to text-2xl, font-medium
  - Body Text: text-base to text-lg
  - UI Elements: text-sm to text-base

## Layout System
**Spacing Units**: Tailwind units of 3, 4, 6, 8, 12, and 16 for consistent rhythm
- Section padding: py-16 (mobile) to py-24 (desktop)
- Component gaps: gap-6 to gap-8
- Container max-width: max-w-7xl with px-4 to px-8

## Core Pages & Sections

### Homepage
1. **Hero Section** (full viewport impact)
   - Large lifestyle image: Model with bone straight hair in elegant setting
   - Headline overlay: "Premium Hair. Perfect Confidence."
   - Dual CTAs: "Shop Collection" + "Payment Plans Available"
   - Trust badge: "Authentic Import Quality"

2. **Featured Collections** (3-column grid)
   - Bone Straights showcase
   - Trending Styles section
   - New Arrivals highlights
   - Each with product imagery, price, and "View Details" button

3. **Installment Payment Spotlight**
   - Visual explainer: "Buy Now, Pay in 2 Installments"
   - Calculator widget showing split payment example
   - Trust indicators for secure payment

4. **Transformation Gallery** (before/after slider or masonry grid)
   - Customer photos showcasing results
   - Instagram-style layout with engagement metrics

5. **Why Choose Us**
   - 4-column grid: Direct Import Quality, Flexible Payment, Fast Lagos Delivery, Expert Support
   - Icons with descriptions

6. **Social Proof Section**
   - Customer testimonials with photos
   - 5-star rating displays
   - Instagram feed integration

7. **Newsletter + WhatsApp CTA**
   - Dual subscription options
   - WhatsApp quick contact for inquiries

### Product Listing Page
- Masonry grid layout (2-3 columns responsive)
- Filters sidebar: Price range, hair type, length, texture
- Sort options: Price, popularity, newest
- Quick view modal for fast browsing
- Prominent "Installment Available" badge on cards

### Product Detail Page
- Large image gallery (swipeable, zoomable)
- Product title, price, installment breakdown immediately visible
- Tabbed sections: Description, Specifications, Care Instructions, Reviews
- "Buy Now" vs "Add to Cart" options
- Installment payment calculator widget
- Related products carousel below
- Trust badges: Authentic guarantee, return policy, secure payment

### Checkout & Order Page (New Age Features)
1. **Progressive Multi-Step Flow**
   - Step indicators: Cart → Delivery → Payment → Confirmation
   - Persistent cart summary sidebar

2. **Installment Payment Selection**
   - Toggle between full payment and split payment
   - Visual breakdown showing payment schedule
   - Auto-calculation of installments

3. **Smart Address Input**
   - Nigerian state/LGA autocomplete
   - Saved addresses for returning customers
   - Delivery time estimates based on location

4. **Payment Integrations**
   - Multiple Nigerian payment gateways
   - Bank transfer instructions
   - WhatsApp payment confirmation option

5. **Order Tracking Enhancement**
   - Real-time status updates
   - SMS/WhatsApp notifications
   - Expected delivery countdown

## Component Library

### Navigation
- Sticky header with search, cart icon (with count badge), account menu
- Mobile: Hamburger menu with slide-out drawer
- Mega menu for desktop product categories

### Cards
- Product cards: Image, title, price, installment info, quick add button
- Elevated shadows on hover
- "New" and "Sale" badges

### Forms
- Floating labels for inputs
- Inline validation with Nigerian phone format (+234)
- CTA buttons: Large, full-width on mobile

### Trust Elements
- Security badges (SSL, payment icons)
- Money-back guarantee seal
- Customer count indicators ("Join 5,000+ satisfied customers")

## Mobile-First Considerations
- Single column layouts on mobile
- Thumb-friendly tap targets (min 44px)
- Bottom-sheet modals for filters and cart
- Sticky "Add to Cart" button on product pages

## Images Strategy
**Hero**: Full-width glamour shot of model with bone straight hair - professional, aspirational
**Products**: Clean white background product shots + lifestyle context images
**Testimonials**: Real customer selfies with their purchased hair
**Features**: Icon illustrations for service benefits
**Gallery**: Before/after transformation grid

## Animations
- Minimal, performance-focused
- Smooth page transitions
- Product image zoom on hover
- Micro-interactions on add-to-cart success

## Marketing Elements Throughout
- Exit-intent popup with discount offer
- Countdown timers for limited offers
- Stock scarcity indicators ("Only 3 left")
- Social proof popups ("Jane from Lagos just purchased...")
- Sticky promotional banner for free delivery threshold
- WhatsApp floating action button for instant contact