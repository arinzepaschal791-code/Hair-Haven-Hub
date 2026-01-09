import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Package, Search, Truck, CheckCircle, Clock, MapPin, CreditCard } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import type { Order, OrderItem } from "@shared/schema";

const statusSteps = [
  { key: "pending", label: "Order Placed", icon: Package },
  { key: "processing", label: "Processing", icon: Clock },
  { key: "shipped", label: "Shipped", icon: Truck },
  { key: "delivered", label: "Delivered", icon: CheckCircle },
];

export default function OrderTracking() {
  const [orderNumber, setOrderNumber] = useState("");
  const [searchId, setSearchId] = useState<string | null>(null);

  const { data: order, isLoading, isError, error } = useQuery<Order>({
    queryKey: ["/api/orders", searchId],
    enabled: !!searchId,
    retry: false,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (orderNumber.trim()) {
      setSearchId(orderNumber.trim().toLowerCase());
    }
  };

  const getOrderItems = (order: Order): OrderItem[] => {
    try {
      return JSON.parse(order.items);
    } catch {
      return [];
    }
  };

  const getStatusIndex = (status: string) => {
    return statusSteps.findIndex((s) => s.key === status);
  };

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Package className="h-8 w-8 text-primary" />
        </div>
        <h1 className="font-serif text-3xl font-bold mb-2">Track Your Order</h1>
        <p className="text-muted-foreground">
          Enter your order number to check the status of your order
        </p>
      </div>

      <Card className="mb-8">
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <Label htmlFor="orderNumber" className="sr-only">Order Number</Label>
              <Input
                id="orderNumber"
                type="text"
                placeholder="Enter order number (e.g., 0FFCF0C3)"
                value={orderNumber}
                onChange={(e) => setOrderNumber(e.target.value)}
                className="w-full"
                data-testid="input-order-number"
              />
            </div>
            <Button type="submit" disabled={!orderNumber.trim()} data-testid="button-track-order">
              <Search className="h-4 w-4 mr-2" />
              Track Order
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardContent className="p-6 space-y-4">
            <Skeleton className="h-8 w-1/2" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
      )}

      {isError && searchId && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="p-6 text-center">
            <p className="text-destructive font-medium mb-2">Order not found</p>
            <p className="text-sm text-muted-foreground">
              Please check your order number and try again. Order numbers are 8 characters long.
            </p>
          </CardContent>
        </Card>
      )}

      {order && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div>
                  <CardTitle className="font-mono text-xl">#{order.id.slice(0, 8).toUpperCase()}</CardTitle>
                  <CardDescription>
                    Placed on {new Date(order.orderDate).toLocaleDateString("en-NG", {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </CardDescription>
                </div>
                <Badge
                  variant={
                    order.orderStatus === "delivered" ? "default" :
                    order.orderStatus === "shipped" ? "secondary" :
                    "outline"
                  }
                  className="capitalize text-sm"
                >
                  {order.orderStatus}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="relative pt-4">
                <div className="flex justify-between relative">
                  {statusSteps.map((step, index) => {
                    const currentIndex = getStatusIndex(order.orderStatus || "pending");
                    const isCompleted = index <= currentIndex;
                    const isCurrent = index === currentIndex;
                    const Icon = step.icon;

                    return (
                      <div key={step.key} className="flex flex-col items-center relative z-10 flex-1">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                            isCompleted
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          } ${isCurrent ? "ring-4 ring-primary/20" : ""}`}
                        >
                          <Icon className="h-5 w-5" />
                        </div>
                        <span
                          className={`text-xs mt-2 text-center ${
                            isCompleted ? "font-medium" : "text-muted-foreground"
                          }`}
                        >
                          {step.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div className="absolute top-9 left-0 right-0 h-0.5 bg-muted -z-0">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{
                      width: `${(getStatusIndex(order.orderStatus || "pending") / (statusSteps.length - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Order Items
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {getOrderItems(order).map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded bg-muted overflow-hidden shrink-0">
                      {item.image && (
                        <img src={item.image} alt={item.productName} className="w-full h-full object-cover" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{item.productName}</p>
                      <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                    </div>
                    <p className="text-sm font-medium">N{(item.price * item.quantity).toLocaleString()}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Payment Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Payment Plan</span>
                  <Badge variant={order.paymentPlan === "installment" ? "default" : "secondary"}>
                    {order.paymentPlan === "installment" ? "Installment" : "Full Payment"}
                  </Badge>
                </div>
                {order.paymentPlan === "installment" ? (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">First Payment (50%)</span>
                      <span className="font-medium">N{order.firstPayment?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Second Payment (50%)</span>
                      <span>N{order.secondPayment?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm pt-2 border-t">
                      <span className="text-muted-foreground">First Payment Status</span>
                      <Badge variant={order.firstPaymentStatus === "paid" ? "default" : "outline"} className="capitalize">
                        {order.firstPaymentStatus}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Second Payment Status</span>
                      <Badge variant={order.secondPaymentStatus === "paid" ? "default" : "outline"} className="capitalize">
                        {order.secondPaymentStatus}
                      </Badge>
                    </div>
                  </>
                ) : (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Payment Status</span>
                    <Badge variant={order.firstPaymentStatus === "paid" ? "default" : "outline"} className="capitalize">
                      {order.firstPaymentStatus}
                    </Badge>
                  </div>
                )}
                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="font-medium">Total Amount</span>
                  <span className="font-bold text-lg">N{order.totalAmount.toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-muted/50">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-4 text-center">
                Need help with your order? Contact us on WhatsApp
              </p>
              <a
                href={`https://wa.me/2348012345678?text=${encodeURIComponent(
                  `Hi! I need help with my order #${order.id.slice(0, 8).toUpperCase()}`
                )}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" className="w-full" data-testid="button-whatsapp-help">
                  <SiWhatsapp className="h-5 w-5 mr-2 text-[#25D366]" />
                  Contact Support
                </Button>
              </a>
            </CardContent>
          </Card>
        </div>
      )}
    </main>
  );
}
