import { Link } from "wouter";
import { useCart } from "@/lib/cart";
import { CartItem } from "@/components/cart/CartItem";
import { CartSummary } from "@/components/cart/CartSummary";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShoppingBag, ArrowRight, Trash2, CreditCard, Calendar, Sparkles } from "lucide-react";

export default function Cart() {
  const { items, clearCart, totalItems, totalAmount } = useCart();

  const deliveryFee = totalAmount >= 150000 ? 0 : 5000;
  const finalTotal = totalAmount + deliveryFee;
  const firstPayment = Math.round(finalTotal / 2);

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
      <div className="flex items-center justify-between gap-4 flex-wrap mb-8">
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
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardContent className="p-6">
              {items.map((item) => (
                <CartItem key={item.id} item={item} />
              ))}
            </CardContent>
          </Card>

          <Card className="border-2 border-primary/30 bg-primary/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Pay in 2 Easy Installments
                <Badge variant="secondary">No Extra Cost</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-2">
              <p className="text-sm text-muted-foreground mb-4">
                Split your payment into two halves. Your order ships immediately after the first payment!
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 bg-background rounded-md border">
                  <div className="rounded-full bg-primary/10 p-2">
                    <CreditCard className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Pay Today</p>
                    <p className="font-bold">N{firstPayment.toLocaleString()}</p>
                  </div>
                  <Badge className="ml-auto">50%</Badge>
                </div>
                <div className="flex items-center gap-3 p-3 bg-background rounded-md border">
                  <div className="rounded-full bg-muted p-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Within 30 Days</p>
                    <p className="font-bold">N{(finalTotal - firstPayment).toLocaleString()}</p>
                  </div>
                  <Badge variant="outline" className="ml-auto">50%</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <CartSummary showInstallmentOption={true} />
          
          <Link href="/checkout">
            <Button className="w-full" size="lg" data-testid="button-checkout">
              Proceed to Checkout
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </Link>

          <p className="text-center text-xs text-muted-foreground">
            Choose installment or full payment at checkout
          </p>

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
