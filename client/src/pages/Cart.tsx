import { Link } from "wouter";
import { useCart } from "@/lib/cart";
import { CartItem } from "@/components/cart/CartItem";
import { CartSummary } from "@/components/cart/CartSummary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ShoppingBag, ArrowRight, Trash2 } from "lucide-react";

export default function Cart() {
  const { items, clearCart, totalItems } = useCart();

  if (items.length === 0) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center max-w-md mx-auto">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-muted mb-6">
            <ShoppingBag className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="font-serif text-2xl font-bold mb-4">Your Cart is Empty</h1>
          <p className="text-muted-foreground mb-8">
            Looks like you haven't added any items to your cart yet. Start shopping to find your perfect hair!
          </p>
          <Link href="/shop">
            <Button size="lg" data-testid="button-start-shopping">
              Start Shopping
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-serif text-3xl font-bold">Shopping Cart</h1>
          <p className="text-muted-foreground">{totalItems} items in your cart</p>
        </div>
        <Button
          variant="ghost"
          className="text-muted-foreground"
          onClick={clearCart}
          data-testid="button-clear-cart"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Clear Cart
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card>
            <CardContent className="p-6">
              {items.map((item) => (
                <CartItem key={item.id} item={item} />
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <CartSummary showInstallmentOption={false} />
          
          <Link href="/checkout">
            <Button className="w-full" size="lg" data-testid="button-checkout">
              Proceed to Checkout
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </Link>

          <Link href="/shop">
            <Button variant="outline" className="w-full" data-testid="button-continue-shopping">
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
