import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Package, MapPin, CreditCard, Copy, Check } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import { Link } from "wouter";
import { useState } from "react";
import type { Order, OrderItem } from "@shared/schema";

interface OrderConfirmationProps {
  order: Order;
  customerEmail: string;
}

export function OrderConfirmation({ order, customerEmail }: OrderConfirmationProps) {
  const [copied, setCopied] = useState(false);
  const items: OrderItem[] = JSON.parse(order.items);
  const isInstallment = order.paymentPlan === "installment";

  const bankDetails = {
    bankName: "GTBank",
    accountNumber: "0123456789",
    accountName: "NORAHAIRLINE Ltd",
  };

  const copyAccountNumber = () => {
    navigator.clipboard.writeText(bankDetails.accountNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
          <CheckCircle className="h-10 w-10 text-green-600" />
        </div>
        <h1 className="font-serif text-3xl font-bold mb-2">Order Placed Successfully!</h1>
        <p className="text-muted-foreground">
          Order confirmation has been sent to {customerEmail}
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-muted-foreground">Order Number</p>
              <p className="font-mono font-bold text-lg">{order.id.slice(0, 8).toUpperCase()}</p>
            </div>
            <Badge variant={isInstallment ? "default" : "secondary"}>
              {isInstallment ? "Installment" : "Full Payment"}
            </Badge>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Package className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Items Ordered</p>
                {items.map((item, index) => (
                  <p key={index} className="text-sm text-muted-foreground">
                    {item.quantity}x {item.productName}
                  </p>
                ))}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CreditCard className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Payment Details</p>
                {isInstallment ? (
                  <>
                    <p className="text-sm text-muted-foreground">
                      First payment due: <span className="font-bold text-primary">N{order.firstPayment?.toLocaleString()}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Second payment: N{order.secondPayment?.toLocaleString()} (within 30 days)
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Total: <span className="font-bold">N{order.totalAmount.toLocaleString()}</span>
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Complete Your Payment
          </h3>

          <div className="bg-background rounded-md p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Bank Name:</span>
              <span className="font-medium">{bankDetails.bankName}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Account Number:</span>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold">{bankDetails.accountNumber}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8"
                  onClick={copyAccountNumber}
                  data-testid="button-copy-account"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Account Name:</span>
              <span className="font-medium">{bankDetails.accountName}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t">
              <span className="text-sm font-medium">Amount to Pay:</span>
              <span className="font-bold text-lg text-primary">
                N{(isInstallment ? order.firstPayment : order.totalAmount)?.toLocaleString()}
              </span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground mt-4">
            Use your order number ({order.id.slice(0, 8).toUpperCase()}) as payment reference
          </p>
        </CardContent>
      </Card>

      <div className="flex flex-col sm:flex-row gap-3">
        <a
          href={`https://wa.me/2348012345678?text=${encodeURIComponent(
            `Hi! I just placed an order #${order.id.slice(0, 8).toUpperCase()} and I've made my payment. Please confirm.`
          )}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1"
        >
          <Button variant="outline" className="w-full" size="lg" data-testid="button-whatsapp-confirm">
            <SiWhatsapp className="h-5 w-5 mr-2 text-[#25D366]" />
            Confirm Payment on WhatsApp
          </Button>
        </a>

        <Link href="/shop" className="flex-1">
          <Button variant="secondary" className="w-full" size="lg" data-testid="button-continue-shopping">
            Continue Shopping
          </Button>
        </Link>
      </div>
    </div>
  );
}
