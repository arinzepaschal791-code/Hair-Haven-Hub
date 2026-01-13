import { Link, useSearch } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle, ShoppingBag, Home } from "lucide-react";

export default function PaymentSuccess() {
  const searchString = useSearch();
  const params = new URLSearchParams(searchString);
  const orderId = params.get("orderId");

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-4 w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <CheckCircle className="h-12 w-12 text-green-600" />
          </div>
          <CardTitle className="font-serif text-2xl text-green-600">
            Payment Successful!
          </CardTitle>
          <CardDescription className="text-base">
            Thank you for your purchase. Your order has been confirmed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {orderId && (
            <div className="p-4 bg-muted rounded-md">
              <p className="text-sm text-muted-foreground">Order Reference</p>
              <p className="font-mono font-bold text-lg">{orderId}</p>
            </div>
          )}

          <div className="p-4 bg-primary/10 rounded-md">
            <p className="text-sm">
              We'll send you an email with your order details and tracking information once your order ships.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-4">
            <Link href="/shop">
              <Button className="w-full" data-testid="button-continue-shopping">
                <ShoppingBag className="h-4 w-4 mr-2" />
                Continue Shopping
              </Button>
            </Link>
            <Link href="/">
              <Button variant="outline" className="w-full" data-testid="button-go-home">
                <Home className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </Link>
          </div>

          <p className="text-xs text-muted-foreground pt-4">
            Need help? Contact us on WhatsApp or email support@norahairline.com
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
