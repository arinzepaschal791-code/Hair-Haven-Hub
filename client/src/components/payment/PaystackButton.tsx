import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { useLocation } from "wouter";
import { CreditCard, Loader2 } from "lucide-react";
import type { Product } from "@shared/schema";

interface PaystackButtonProps {
  product: Product;
  quantity: number;
}

export function PaystackButton({ product, quantity }: PaystackButtonProps) {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [phone, setPhone] = useState("");

  const totalAmount = product.price * quantity;

  const handlePayment = async () => {
    if (!email || !customerName) {
      toast({
        title: "Please fill in required fields",
        description: "Email and name are required to process payment.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const configResponse = await fetch("/api/paystack/config", {
        credentials: "include",
      });
      const configData = await configResponse.json();

      if (!configData.publicKey) {
        throw new Error("Payment system not configured");
      }

      const initResponse = await apiRequest("POST", "/api/paystack/initialize", {
        email,
        amount: totalAmount,
        productId: product.id,
        productName: product.name,
        quantity,
        customerName,
        phone,
      });
      const paymentData = await initResponse.json();

      const PaystackPop = (window as any).PaystackPop;
      if (!PaystackPop) {
        throw new Error("Paystack script not loaded");
      }

      const handler = PaystackPop.setup({
        key: configData.publicKey,
        email: paymentData.email,
        amount: paymentData.amount,
        currency: paymentData.currency,
        ref: paymentData.reference,
        metadata: {
          custom_fields: [
            {
              display_name: "Customer Name",
              variable_name: "customer_name",
              value: customerName,
            },
            {
              display_name: "Product",
              variable_name: "product_name",
              value: product.name,
            },
          ],
        },
        onClose: () => {
          setIsLoading(false);
          toast({
            title: "Payment cancelled",
            description: "You closed the payment window.",
          });
        },
        callback: async (response: { reference: string }) => {
          try {
            const verifyResponse = await apiRequest("POST", "/api/paystack/verify", {
              reference: response.reference,
            });
            const verifyData = await verifyResponse.json();

            if (verifyData.success) {
              setIsDialogOpen(false);
              setLocation(`/payment-success?orderId=${verifyData.orderId}`);
            } else {
              setLocation(`/payment-failed?reference=${response.reference}`);
            }
          } catch (error) {
            setLocation(`/payment-failed?reference=${response.reference}`);
          }
          setIsLoading(false);
        },
      });

      handler.openIframe();
    } catch (error: any) {
      setIsLoading(false);
      toast({
        title: "Payment error",
        description: error.message || "Failed to initialize payment",
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <Button
        className="w-full"
        size="lg"
        onClick={() => setIsDialogOpen(true)}
        disabled={!product.inStock}
        data-testid="button-buy-now-paystack"
      >
        <CreditCard className="h-5 w-5 mr-2" />
        Buy Now - Pay with Paystack
      </Button>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-serif">Complete Your Purchase</DialogTitle>
            <DialogDescription>
              Enter your details to pay for {product.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="p-4 bg-muted rounded-md">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Product:</span>
                <span className="font-medium">{product.name}</span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-muted-foreground">Quantity:</span>
                <span className="font-medium">{quantity}</span>
              </div>
              <div className="flex justify-between items-center mt-2 pt-2 border-t">
                <span className="font-bold">Total:</span>
                <span className="font-bold text-primary">
                  N{totalAmount.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="customerName">Full Name *</Label>
              <Input
                id="customerName"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Enter your full name"
                data-testid="input-customer-name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                data-testid="input-email"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number (Optional)</Label>
              <Input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Enter your phone number"
                data-testid="input-phone"
              />
            </div>

            <Button
              className="w-full"
              size="lg"
              onClick={handlePayment}
              disabled={isLoading || !email || !customerName}
              data-testid="button-proceed-payment"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CreditCard className="h-5 w-5 mr-2" />
                  Pay N{totalAmount.toLocaleString()}
                </>
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Secure payment powered by Paystack. We never store your card details.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
