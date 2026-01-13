import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertProductSchema, insertOrderSchema, insertSubscriberSchema, nigerianStates, lagosLGAs, abujLGAs } from "@shared/schema";
import bcrypt from "bcrypt";
import multer from "multer";
import path from "path";
import fs from "fs";
import { registerObjectStorageRoutes } from "./replit_integrations/object_storage";

declare module "express-session" {
  interface SessionData {
    adminId?: string;
    isAdmin?: boolean;
  }
}

const uploadDir = path.join(process.cwd(), "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage_multer = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  },
});

const imageUpload = multer({
  storage: storage_multer,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    if (extname && mimetype) {
      return cb(null, true);
    }
    cb(new Error("Only image files are allowed"));
  },
});

const videoUpload = multer({
  storage: storage_multer,
  limits: { fileSize: 100 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /mp4|webm|mov|avi/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = file.mimetype.startsWith("video/");
    if (extname && mimetype) {
      return cb(null, true);
    }
    cb(new Error("Only video files are allowed"));
  },
});

const mediaUpload = multer({
  storage: storage_multer,
  limits: { fileSize: 100 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const imageTypes = /jpeg|jpg|png|gif|webp/;
    const videoTypes = /mp4|webm|mov|avi/;
    const ext = path.extname(file.originalname).toLowerCase();
    const isImage = imageTypes.test(ext) && (file.mimetype.startsWith("image/") || imageTypes.test(file.mimetype));
    const isVideo = videoTypes.test(ext) && file.mimetype.startsWith("video/");
    if (isImage || isVideo) {
      return cb(null, true);
    }
    cb(new Error("Only image and video files are allowed"));
  },
});

function requireAdmin(req: Request, res: Response, next: NextFunction) {
  if (req.session && req.session.isAdmin) {
    next();
  } else {
    res.status(401).json({ error: "Unauthorized - Admin access required" });
  }
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  // Register object storage routes for permanent file uploads
  registerObjectStorageRoutes(app);
  
  // Admin authentication endpoints
  app.post("/api/admin/login", async (req, res) => {
    try {
      const { username, password } = req.body;
      if (!username || !password) {
        return res.status(400).json({ error: "Username and password required" });
      }

      const admin = await storage.getAdminByUsername(username);
      if (!admin) {
        return res.status(401).json({ error: "Invalid credentials" });
      }

      const validPassword = await bcrypt.compare(password, admin.password);
      if (!validPassword) {
        return res.status(401).json({ error: "Invalid credentials" });
      }

      req.session.adminId = admin.id;
      req.session.isAdmin = true;
      
      res.json({ message: "Login successful", admin: { id: admin.id, username: admin.username } });
    } catch (error) {
      console.error("Login error:", error);
      res.status(500).json({ error: "Login failed" });
    }
  });

  app.post("/api/admin/logout", (req, res) => {
    req.session.destroy((err) => {
      if (err) {
        return res.status(500).json({ error: "Logout failed" });
      }
      res.json({ message: "Logged out successfully" });
    });
  });

  app.get("/api/admin/session", (req, res) => {
    if (req.session && req.session.isAdmin) {
      res.json({ isAdmin: true, adminId: req.session.adminId });
    } else {
      res.json({ isAdmin: false });
    }
  });

  app.post("/api/admin/setup", async (req, res) => {
    try {
      const existingAdmin = await storage.getAdminByUsername("admin");
      if (existingAdmin) {
        return res.status(400).json({ error: "Admin already exists" });
      }

      const { password } = req.body;
      if (!password || password.length < 6) {
        return res.status(400).json({ error: "Password must be at least 6 characters" });
      }

      const hashedPassword = await bcrypt.hash(password, 10);
      const admin = await storage.createAdminUser({
        username: "admin",
        password: hashedPassword,
      });

      res.status(201).json({ message: "Admin account created", admin: { id: admin.id, username: admin.username } });
    } catch (error) {
      console.error("Admin setup error:", error);
      res.status(500).json({ error: "Failed to create admin" });
    }
  });

  // Image upload endpoint (single)
  app.post("/api/upload/image", requireAdmin, imageUpload.single("file"), (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }
      const imageUrl = `/uploads/${req.file.filename}`;
      res.json({ url: imageUrl, type: "image" });
    } catch (error) {
      res.status(500).json({ error: "Upload failed" });
    }
  });

  // Multiple images upload endpoint
  app.post("/api/upload/images", requireAdmin, imageUpload.array("files", 10), (req, res) => {
    try {
      const files = req.files as Express.Multer.File[];
      if (!files || files.length === 0) {
        return res.status(400).json({ error: "No files uploaded" });
      }
      const urls = files.map((file) => `/uploads/${file.filename}`);
      res.json({ urls, type: "image" });
    } catch (error) {
      res.status(500).json({ error: "Upload failed" });
    }
  });

  // Video upload endpoint
  app.post("/api/upload/video", requireAdmin, videoUpload.single("file"), (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }
      const videoUrl = `/uploads/${req.file.filename}`;
      res.json({ url: videoUrl, type: "video" });
    } catch (error) {
      res.status(500).json({ error: "Upload failed" });
    }
  });

  // Generic media upload (images or video)
  app.post("/api/upload/media", requireAdmin, mediaUpload.single("file"), (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }
      const mediaUrl = `/uploads/${req.file.filename}`;
      const isVideo = req.file.mimetype.startsWith("video/");
      res.json({ url: mediaUrl, type: isVideo ? "video" : "image" });
    } catch (error) {
      res.status(500).json({ error: "Upload failed" });
    }
  });

  // Products endpoints
  app.get("/api/products", async (req, res) => {
    try {
      const products = await storage.getAllProducts();
      res.json(products);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch products" });
    }
  });

  app.get("/api/products/:id", async (req, res) => {
    try {
      const product = await storage.getProduct(req.params.id);
      if (!product) {
        return res.status(404).json({ error: "Product not found" });
      }
      res.json(product);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch product" });
    }
  });

  app.post("/api/products", requireAdmin, async (req, res) => {
    try {
      const parsed = insertProductSchema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: "Invalid product data", details: parsed.error });
      }
      const product = await storage.createProduct(parsed.data);
      res.status(201).json(product);
    } catch (error) {
      res.status(500).json({ error: "Failed to create product" });
    }
  });

  app.patch("/api/products/:id", requireAdmin, async (req, res) => {
    try {
      const parsed = insertProductSchema.partial().safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: "Invalid product data", details: parsed.error });
      }
      const product = await storage.updateProduct(req.params.id, parsed.data);
      if (!product) {
        return res.status(404).json({ error: "Product not found" });
      }
      res.json(product);
    } catch (error) {
      res.status(500).json({ error: "Failed to update product" });
    }
  });

  app.delete("/api/products/:id", requireAdmin, async (req, res) => {
    try {
      const deleted = await storage.deleteProduct(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Product not found" });
      }
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: "Failed to delete product" });
    }
  });

  // Orders endpoints (admin protected)
  app.get("/api/orders", requireAdmin, async (req, res) => {
    try {
      const orders = await storage.getAllOrders();
      res.json(orders);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch orders" });
    }
  });

  app.get("/api/orders/:id", async (req, res) => {
    try {
      const order = await storage.getOrder(req.params.id);
      if (!order) {
        return res.status(404).json({ error: "Order not found" });
      }
      res.json(order);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch order" });
    }
  });

  app.post("/api/orders", async (req, res) => {
    try {
      const orderData = {
        customerId: req.body.customerId || "guest",
        addressId: req.body.addressId || "new",
        items: req.body.items,
        totalAmount: req.body.totalAmount,
        paymentPlan: req.body.paymentPlan,
        firstPayment: req.body.firstPayment,
        secondPayment: req.body.secondPayment,
        firstPaymentStatus: "pending",
        secondPaymentStatus: "pending",
        orderStatus: "pending",
        orderDate: req.body.orderDate || new Date().toISOString(),
      };

      const order = await storage.createOrder(orderData);
      res.status(201).json(order);
    } catch (error) {
      console.error("Order creation error:", error);
      res.status(500).json({ error: "Failed to create order" });
    }
  });

  app.patch("/api/orders/:id/status", requireAdmin, async (req, res) => {
    try {
      const { status } = req.body;
      const order = await storage.updateOrderStatus(req.params.id, status);
      if (!order) {
        return res.status(404).json({ error: "Order not found" });
      }
      res.json(order);
    } catch (error) {
      res.status(500).json({ error: "Failed to update order status" });
    }
  });

  // Testimonials endpoints
  app.get("/api/testimonials", async (req, res) => {
    try {
      const testimonials = await storage.getAllTestimonials();
      res.json(testimonials);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch testimonials" });
    }
  });

  // Newsletter subscription
  app.post("/api/subscribe", async (req, res) => {
    try {
      const parsed = insertSubscriberSchema.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: "Invalid subscriber data" });
      }
      const subscriber = await storage.createSubscriber(parsed.data);
      res.status(201).json(subscriber);
    } catch (error) {
      res.status(500).json({ error: "Failed to subscribe" });
    }
  });

  // Nigerian states and LGAs lookup
  app.get("/api/meta/states", (req, res) => {
    res.json(nigerianStates);
  });

  app.get("/api/meta/lgas", (req, res) => {
    const { state } = req.query;
    if (state === "Lagos") {
      res.json(lagosLGAs);
    } else if (state === "FCT") {
      res.json(abujLGAs);
    } else {
      res.json([]);
    }
  });

  // ===== PAYSTACK PAYMENT INTEGRATION =====
  // These routes handle payment processing with Paystack
  
  // Get Paystack public key (safe to expose to frontend)
  app.get("/api/paystack/config", (req, res) => {
    // Return the public key for frontend Paystack popup
    // This key is safe to share - it can only initialize payments, not verify them
    const publicKey = process.env.PAYSTACK_PUBLIC_KEY;
    if (!publicKey) {
      return res.status(500).json({ error: "Paystack not configured" });
    }
    res.json({ publicKey });
  });

  // Initialize a payment - creates an order and returns payment reference
  app.post("/api/paystack/initialize", async (req, res) => {
    try {
      const { email, amount, productId, productName, quantity, customerName, phone } = req.body;

      // Validate required fields
      if (!email || !amount || !productId || !productName) {
        return res.status(400).json({ error: "Missing required fields: email, amount, productId, productName" });
      }

      // Create a unique reference for this transaction
      // Format: NORA-timestamp-random for easy identification
      const reference = `NORA-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

      // Create the order in database with pending payment status
      const orderData = {
        customerId: email, // Use email as customer ID for now
        addressId: "pending", // Will be updated during checkout
        items: JSON.stringify([{
          productId,
          productName,
          price: amount,
          quantity: quantity || 1,
          image: ""
        }]),
        totalAmount: amount,
        paymentPlan: "full",
        firstPayment: amount,
        secondPayment: 0,
        firstPaymentStatus: "pending",
        secondPaymentStatus: "paid",
        orderStatus: "pending",
        orderDate: new Date().toISOString(),
        paystackReference: reference,
        paymentStatus: "unpaid",
      };

      const order = await storage.createOrder(orderData);

      // Return data needed for Paystack popup
      res.json({
        reference,
        orderId: order.id,
        amount: amount * 100, // Paystack expects amount in kobo (smallest currency unit)
        email,
        currency: "NGN",
      });
    } catch (error) {
      console.error("Payment initialization error:", error);
      res.status(500).json({ error: "Failed to initialize payment" });
    }
  });

  // Verify payment after Paystack popup completes
  // This is called from frontend after user completes payment
  app.post("/api/paystack/verify", async (req, res) => {
    try {
      const { reference } = req.body;

      if (!reference) {
        return res.status(400).json({ error: "Payment reference is required" });
      }

      // Get Paystack secret key from environment (NEVER expose this to frontend!)
      const secretKey = process.env.PAYSTACK_SECRET_KEY;
      if (!secretKey) {
        return res.status(500).json({ error: "Paystack not configured" });
      }

      // Verify the payment with Paystack API
      // This confirms the payment was actually made
      const verifyResponse = await fetch(
        `https://api.paystack.co/transaction/verify/${reference}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${secretKey}`,
            "Content-Type": "application/json",
          },
        }
      );

      const verifyData = await verifyResponse.json();

      // Check if verification was successful
      if (!verifyData.status) {
        return res.status(400).json({ 
          error: "Payment verification failed", 
          message: verifyData.message 
        });
      }

      // Check if the payment was actually successful
      const paymentData = verifyData.data;
      if (paymentData.status !== "success") {
        // Update order with failed payment status
        const order = await storage.getOrderByReference(reference);
        if (order) {
          await storage.updateOrderPayment(order.id, "failed");
        }
        return res.status(400).json({ 
          success: false,
          error: "Payment was not successful",
          status: paymentData.status
        });
      }

      // Payment successful! Update the order in database
      const order = await storage.getOrderByReference(reference);
      if (!order) {
        return res.status(404).json({ error: "Order not found" });
      }

      // Mark order as paid
      await storage.updateOrderPayment(order.id, "paid", new Date().toISOString());
      await storage.updateOrderStatus(order.id, "processing");

      res.json({
        success: true,
        message: "Payment verified successfully",
        orderId: order.id,
        amount: paymentData.amount / 100, // Convert back from kobo to Naira
        reference: paymentData.reference,
        paidAt: paymentData.paid_at,
      });
    } catch (error) {
      console.error("Payment verification error:", error);
      res.status(500).json({ error: "Failed to verify payment" });
    }
  });

  // Paystack webhook - receives notifications directly from Paystack
  // This is a backup verification method with HMAC signature verification
  app.post("/api/paystack/webhook", async (req, res) => {
    try {
      const secretKey = process.env.PAYSTACK_SECRET_KEY;
      
      if (!secretKey) {
        console.error("Webhook error: Paystack secret key not configured");
        return res.sendStatus(500);
      }

      // Get the signature from Paystack headers
      const signature = req.headers["x-paystack-signature"] as string;
      
      if (!signature) {
        console.error("Webhook rejected: Missing x-paystack-signature header");
        return res.sendStatus(400);
      }

      // Verify the HMAC signature to ensure request is from Paystack
      // Paystack uses HMAC SHA512 with the secret key
      const crypto = await import("crypto");
      const rawBody = (req as any).rawBody;
      
      if (!rawBody) {
        console.error("Webhook error: Raw body not available for signature verification");
        return res.sendStatus(400);
      }

      const expectedSignature = crypto
        .createHmac("sha512", secretKey)
        .update(rawBody)
        .digest("hex");

      // Compare signatures securely (constant-time comparison)
      if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
        console.error("Webhook rejected: Invalid signature - request may be forged");
        return res.sendStatus(401);
      }

      // Signature verified - process the event
      const event = req.body;

      // Handle successful charge event
      if (event.event === "charge.success") {
        const paymentData = event.data;
        const reference = paymentData.reference;
        const amountInKobo = paymentData.amount;
        const currency = paymentData.currency;

        // Find the order by reference
        const order = await storage.getOrderByReference(reference);
        
        if (!order) {
          console.error(`Webhook: Order not found for reference ${reference}`);
          return res.sendStatus(200); // Still return 200 to prevent retries
        }

        // Verify amount matches (convert order amount to kobo for comparison)
        const expectedAmountKobo = Math.round(order.totalAmount * 100);
        if (amountInKobo !== expectedAmountKobo) {
          console.error(`Webhook: Amount mismatch for ${reference}. Expected ${expectedAmountKobo}, got ${amountInKobo}`);
          return res.sendStatus(200); // Return 200 but don't update
        }

        // Verify currency is NGN
        if (currency !== "NGN") {
          console.error(`Webhook: Currency mismatch for ${reference}. Expected NGN, got ${currency}`);
          return res.sendStatus(200);
        }

        // All checks passed - update order if not already paid
        if (order.paymentStatus !== "paid") {
          await storage.updateOrderPayment(order.id, "paid", new Date().toISOString());
          await storage.updateOrderStatus(order.id, "processing");
          console.log(`Webhook: Order ${order.id} marked as paid via webhook`);
        }
      }

      res.sendStatus(200);
    } catch (error) {
      console.error("Webhook error:", error);
      res.sendStatus(500);
    }
  });

  return httpServer;
}
