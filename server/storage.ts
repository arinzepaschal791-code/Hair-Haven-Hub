import {
  type User,
  type InsertUser,
  type Product,
  type InsertProduct,
  type Customer,
  type InsertCustomer,
  type Address,
  type InsertAddress,
  type Order,
  type InsertOrder,
  type Testimonial,
  type InsertTestimonial,
  type Subscriber,
  type InsertSubscriber,
  type CartItem,
  type InsertCartItem,
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  getAllProducts(): Promise<Product[]>;
  getProduct(id: string): Promise<Product | undefined>;
  createProduct(product: InsertProduct): Promise<Product>;
  updateProduct(id: string, product: Partial<InsertProduct>): Promise<Product | undefined>;
  deleteProduct(id: string): Promise<boolean>;
  getProductsByCategory(category: string): Promise<Product[]>;

  getCustomer(id: string): Promise<Customer | undefined>;
  getCustomerByEmail(email: string): Promise<Customer | undefined>;
  createCustomer(customer: InsertCustomer): Promise<Customer>;

  getAddresses(customerId: string): Promise<Address[]>;
  createAddress(address: InsertAddress): Promise<Address>;

  getAllOrders(): Promise<Order[]>;
  getOrder(id: string): Promise<Order | undefined>;
  getOrdersByCustomer(customerId: string): Promise<Order[]>;
  createOrder(order: InsertOrder): Promise<Order>;
  updateOrderStatus(id: string, status: string): Promise<Order | undefined>;

  getAllTestimonials(): Promise<Testimonial[]>;
  createTestimonial(testimonial: InsertTestimonial): Promise<Testimonial>;

  createSubscriber(subscriber: InsertSubscriber): Promise<Subscriber>;

  getCartItems(sessionId: string): Promise<CartItem[]>;
  addCartItem(item: InsertCartItem): Promise<CartItem>;
  updateCartItem(id: string, quantity: number): Promise<CartItem | undefined>;
  removeCartItem(id: string): Promise<boolean>;
  clearCart(sessionId: string): Promise<boolean>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private products: Map<string, Product>;
  private customers: Map<string, Customer>;
  private addresses: Map<string, Address>;
  private orders: Map<string, Order>;
  private testimonials: Map<string, Testimonial>;
  private subscribers: Map<string, Subscriber>;
  private cartItems: Map<string, CartItem>;

  constructor() {
    this.users = new Map();
    this.products = new Map();
    this.customers = new Map();
    this.addresses = new Map();
    this.orders = new Map();
    this.testimonials = new Map();
    this.subscribers = new Map();
    this.cartItems = new Map();

    this.seedProducts();
    this.seedTestimonials();
  }

  private seedProducts() {
    const sampleProducts: InsertProduct[] = [
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

    sampleProducts.forEach((product) => {
      const id = randomUUID();
      this.products.set(id, { ...product, id });
    });
  }

  private seedTestimonials() {
    const sampleTestimonials: InsertTestimonial[] = [
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
        content: "Fast delivery and the hair quality exceeded my expectations. Will definitely be ordering again. Thank you GlowHair!",
        rating: 5,
        productPurchased: "Bone Straight 18\"",
      },
    ];

    sampleTestimonials.forEach((testimonial) => {
      const id = randomUUID();
      this.testimonials.set(id, { ...testimonial, id });
    });
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async getAllProducts(): Promise<Product[]> {
    return Array.from(this.products.values());
  }

  async getProduct(id: string): Promise<Product | undefined> {
    return this.products.get(id);
  }

  async createProduct(insertProduct: InsertProduct): Promise<Product> {
    const id = randomUUID();
    const product: Product = { ...insertProduct, id };
    this.products.set(id, product);
    return product;
  }

  async updateProduct(id: string, updates: Partial<InsertProduct>): Promise<Product | undefined> {
    const product = this.products.get(id);
    if (!product) return undefined;
    const updated = { ...product, ...updates };
    this.products.set(id, updated);
    return updated;
  }

  async deleteProduct(id: string): Promise<boolean> {
    return this.products.delete(id);
  }

  async getProductsByCategory(category: string): Promise<Product[]> {
    return Array.from(this.products.values()).filter(
      (product) => product.category === category
    );
  }

  async getCustomer(id: string): Promise<Customer | undefined> {
    return this.customers.get(id);
  }

  async getCustomerByEmail(email: string): Promise<Customer | undefined> {
    return Array.from(this.customers.values()).find(
      (customer) => customer.email === email
    );
  }

  async createCustomer(insertCustomer: InsertCustomer): Promise<Customer> {
    const id = randomUUID();
    const customer: Customer = { ...insertCustomer, id };
    this.customers.set(id, customer);
    return customer;
  }

  async getAddresses(customerId: string): Promise<Address[]> {
    return Array.from(this.addresses.values()).filter(
      (address) => address.customerId === customerId
    );
  }

  async createAddress(insertAddress: InsertAddress): Promise<Address> {
    const id = randomUUID();
    const address: Address = { ...insertAddress, id };
    this.addresses.set(id, address);
    return address;
  }

  async getAllOrders(): Promise<Order[]> {
    return Array.from(this.orders.values());
  }

  async getOrder(id: string): Promise<Order | undefined> {
    return this.orders.get(id);
  }

  async getOrdersByCustomer(customerId: string): Promise<Order[]> {
    return Array.from(this.orders.values()).filter(
      (order) => order.customerId === customerId
    );
  }

  async createOrder(insertOrder: InsertOrder): Promise<Order> {
    const id = randomUUID();
    const order: Order = { ...insertOrder, id };
    this.orders.set(id, order);
    return order;
  }

  async updateOrderStatus(id: string, status: string): Promise<Order | undefined> {
    const order = this.orders.get(id);
    if (!order) return undefined;
    const updated = { ...order, orderStatus: status };
    this.orders.set(id, updated);
    return updated;
  }

  async getAllTestimonials(): Promise<Testimonial[]> {
    return Array.from(this.testimonials.values());
  }

  async createTestimonial(insertTestimonial: InsertTestimonial): Promise<Testimonial> {
    const id = randomUUID();
    const testimonial: Testimonial = { ...insertTestimonial, id };
    this.testimonials.set(id, testimonial);
    return testimonial;
  }

  async createSubscriber(insertSubscriber: InsertSubscriber): Promise<Subscriber> {
    const id = randomUUID();
    const subscriber: Subscriber = { ...insertSubscriber, id };
    this.subscribers.set(id, subscriber);
    return subscriber;
  }

  async getCartItems(sessionId: string): Promise<CartItem[]> {
    return Array.from(this.cartItems.values()).filter(
      (item) => item.sessionId === sessionId
    );
  }

  async addCartItem(insertCartItem: InsertCartItem): Promise<CartItem> {
    const id = randomUUID();
    const cartItem: CartItem = { ...insertCartItem, id };
    this.cartItems.set(id, cartItem);
    return cartItem;
  }

  async updateCartItem(id: string, quantity: number): Promise<CartItem | undefined> {
    const item = this.cartItems.get(id);
    if (!item) return undefined;
    const updated = { ...item, quantity };
    this.cartItems.set(id, updated);
    return updated;
  }

  async removeCartItem(id: string): Promise<boolean> {
    return this.cartItems.delete(id);
  }

  async clearCart(sessionId: string): Promise<boolean> {
    const items = await this.getCartItems(sessionId);
    items.forEach((item) => this.cartItems.delete(item.id));
    return true;
  }
}

export const storage = new MemStorage();
