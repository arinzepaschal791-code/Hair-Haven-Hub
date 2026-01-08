import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Truck, Shield, CreditCard } from "lucide-react";
import { useCart } from "@/lib/cart";

interface CartSummaryProps {
  showInstallmentOption?: boolean;
  paymentPlan?: "full" | "installment";
}

export function CartSummary({ showInstallmentOption = true, paymentPlan = "full" }: CartSummaryProps) {
  const { items, totalAmount } = useCart();
  
  const deliveryFee = totalAmount >= 150000 ? 0 : 5000;
  const finalTotal = totalAmount + deliveryFee;
  const firstPayment = Math.round(finalTotal / 2);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Order Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                {item.product.name} x {item.quantity}
              </span>
              <span>N{(item.product.price * item.quantity).toLocaleString()}</span>
            </div>
          ))}
        </div>

        <Separator />

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Subtotal</span>
            <span>N{totalAmount.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Delivery</span>
            {deliveryFee === 0 ? (
              <span className="text-green-600 font-medium">FREE</span>
            ) : (
              <span>N{deliveryFee.toLocaleString()}</span>
            )}
          </div>
        </div>

        <Separator />

        <div className="flex justify-between font-bold text-lg">
          <span>Total</span>
          <span>N{finalTotal.toLocaleString()}</span>
        </div>

        {showInstallmentOption && paymentPlan === "installment" && (
          <div className="bg-primary/10 rounded-md p-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <CreditCard className="h-4 w-4 text-primary" />
              <span>Installment Payment</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Pay today (50%)</span>
              <span className="font-bold text-primary">
                N{firstPayment.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>Pay within 30 days</span>
              <span>N{(finalTotal - firstPayment).toLocaleString()}</span>
            </div>
          </div>
        )}

        <div className="space-y-2 pt-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Truck className="h-4 w-4" />
            <span>Free delivery on orders above N150,000</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span>Secure checkout guaranteed</span>
          </div>
        </div>

        {totalAmount > 0 && totalAmount < 150000 && (
          <div className="bg-muted rounded-md p-3">
            <p className="text-xs text-muted-foreground">
              Add N{(150000 - totalAmount).toLocaleString()} more to get{" "}
              <Badge variant="secondary" className="text-xs">FREE DELIVERY</Badge>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
