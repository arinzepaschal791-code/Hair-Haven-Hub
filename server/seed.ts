import { db } from "./db";
import { products, testimonials } from "@shared/schema";

const sampleProducts = [
  {
    name: "Premium Bone Straight 22 Inches",
    description: "Luxurious bone straight human hair bundle. Silky smooth texture that stays sleek even after washing. Perfect for a polished, elegant look. Double drawn for full ends.",
    price: 120000,
    category: "bone-straight",
    length: "22 inches",
    texture: "straight",
    images: ["/assets/stock_images/woman_long_straight__87475d1c.jpg"],
    inStock: true,
    stockCount: 15,
    featured: true,
    badge: "Best Seller",
  },
  {
    name: "Bone Straight Bundle 18 Inches",
    description: "High-quality bone straight hair bundle. Smooth, sleek and perfect for any occasion. Minimal shedding and tangling.",
    price: 95000,
    category: "bone-straight",
    length: "18 inches",
    texture: "straight",
    images: ["/assets/stock_images/woman_long_straight__eee03e54.jpg"],
    inStock: true,
    stockCount: 20,
    featured: true,
    badge: "New",
  },
  {
    name: "Luxury Frontal Wig",
    description: "Premium 13x4 lace frontal wig with bone straight hair. Pre-plucked hairline for a natural look. Bleached knots. Ready to wear glamour.",
    price: 180000,
    category: "wig",
    length: "20 inches",
    texture: "straight",
    images: ["/assets/stock_images/beautiful_african_wo_7f5bcd22.jpg"],
    inStock: true,
    stockCount: 8,
    featured: true,
    badge: "Premium",
  },
  {
    name: "Closure Wig - Body Wave",
    description: "Beautiful 4x4 closure wig with body wave texture. Natural-looking hairline. Perfect for beginners. Easy to install.",
    price: 135000,
    category: "wig",
    length: "16 inches",
    texture: "body-wave",
    images: ["/assets/stock_images/beautiful_african_wo_8e308ce0.jpg"],
    inStock: true,
    stockCount: 12,
    featured: true,
  },
  {
    name: "Bone Straight 14 Inches",
    description: "Short and chic bone straight bundle. Great for bob styles and quick installs. 100% human hair.",
    price: 65000,
    category: "bone-straight",
    length: "14 inches",
    texture: "straight",
    images: ["/assets/stock_images/woman_long_straight__1bf9cbec.jpg"],
    inStock: true,
    stockCount: 25,
    featured: false,
  },
  {
    name: "Deep Wave Wig 22 Inches",
    description: "Gorgeous deep wave full lace wig. Voluminous curls that last. Pre-styled and ready to wear.",
    price: 195000,
    category: "wig",
    length: "22 inches",
    texture: "deep-wave",
    images: ["/assets/stock_images/beautiful_african_wo_217fa6d2.jpg"],
    inStock: true,
    stockCount: 5,
    featured: false,
    badge: "Limited",
  },
  {
    name: "Premium Hair Serum",
    description: "Lightweight nourishing serum for human hair extensions. Adds shine without weighing down. Protects from heat damage.",
    price: 12000,
    category: "hair-care",
    images: ["/assets/stock_images/hair_care_products_b_dceab05b.jpg"],
    inStock: true,
    stockCount: 50,
    featured: false,
  },
  {
    name: "Silk Edge Control",
    description: "Professional edge control for sleek styling. Long-lasting hold without flaking. Keeps baby hairs laid all day.",
    price: 8500,
    category: "hair-care",
    images: ["/assets/stock_images/hair_care_products_b_5c926556.jpg"],
    inStock: true,
    stockCount: 40,
    featured: false,
  },
];

const sampleTestimonials = [
  {
    customerName: "Amara Okonkwo",
    location: "Lagos",
    content: "The bone straight hair I got is absolutely amazing! It's been 6 months and it still looks brand new. Best hair vendor in Nigeria!",
    rating: 5,
    productPurchased: "Bone Straight 22\"",
  },
  {
    customerName: "Blessing Eze",
    location: "Abuja",
    content: "The installment payment option was a lifesaver. I got my dream wig without breaking the bank. Customer service is top-notch too!",
    rating: 5,
    productPurchased: "Luxury Frontal Wig",
  },
  {
    customerName: "Chidinma Nwachukwu",
    location: "Port Harcourt",
    content: "Fast delivery and the hair quality exceeded my expectations. Will definitely be ordering again. Thank you NORAHAIRLINE!",
    rating: 5,
    productPurchased: "Bone Straight 18\"",
  },
];

async function seed() {
  console.log("Starting database seed...");

  try {
    const existingProducts = await db.select().from(products);
    if (existingProducts.length === 0) {
      console.log("Seeding products...");
      await db.insert(products).values(sampleProducts);
      console.log(`Inserted ${sampleProducts.length} products`);
    } else {
      console.log(`Products already exist (${existingProducts.length} found), skipping...`);
    }

    const existingTestimonials = await db.select().from(testimonials);
    if (existingTestimonials.length === 0) {
      console.log("Seeding testimonials...");
      await db.insert(testimonials).values(sampleTestimonials);
      console.log(`Inserted ${sampleTestimonials.length} testimonials`);
    } else {
      console.log(`Testimonials already exist (${existingTestimonials.length} found), skipping...`);
    }

    console.log("Database seed completed!");
  } catch (error) {
    console.error("Seed error:", error);
    throw error;
  }
}

seed().then(() => process.exit(0)).catch(() => process.exit(1));
