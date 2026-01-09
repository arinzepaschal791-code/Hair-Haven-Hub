import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/lib/theme";
import { CartProvider } from "@/lib/cart";
import { WishlistProvider } from "@/lib/wishlist";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PromoBar } from "@/components/layout/PromoBar";
import { WhatsAppFAB } from "@/components/layout/WhatsAppFAB";
import { SocialProof } from "@/components/home/SocialProof";
import Home from "@/pages/Home";
import Shop from "@/pages/Shop";
import ProductDetail from "@/pages/ProductDetail";
import Cart from "@/pages/Cart";
import Checkout from "@/pages/Checkout";
import Admin from "@/pages/Admin";
import AdminLogin from "@/pages/AdminLogin";
import About from "@/pages/About";
import Wishlist from "@/pages/Wishlist";
import CategoryPage from "@/pages/CategoryPage";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/shop" component={Shop} />
      <Route path="/product/:id" component={ProductDetail} />
      <Route path="/bone-straight">
        <CategoryPage
          category="bone-straight"
          title="Bone Straight Hair"
          description="Premium silky smooth bone straight hair bundles - the ultimate in sleek perfection"
        />
      </Route>
      <Route path="/wigs">
        <CategoryPage
          category="wig"
          title="Luxury Wigs"
          description="Ready-to-wear glamour - premium quality wigs for every occasion"
        />
      </Route>
      <Route path="/cart" component={Cart} />
      <Route path="/checkout" component={Checkout} />
      <Route path="/wishlist" component={Wishlist} />
      <Route path="/admin/login" component={AdminLogin} />
      <Route path="/admin" component={Admin} />
      <Route path="/about" component={About} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <CartProvider>
          <WishlistProvider>
            <TooltipProvider>
              <div className="min-h-screen flex flex-col bg-background">
                <PromoBar />
                <Header />
                <div className="flex-1">
                  <Router />
                </div>
                <Footer />
                <WhatsAppFAB />
                <SocialProof />
              </div>
              <Toaster />
            </TooltipProvider>
          </WishlistProvider>
        </CartProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
