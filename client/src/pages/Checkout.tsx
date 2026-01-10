import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { useCart } from "@/lib/cart";
import { useToast } from "@/hooks/use-toast";
import { CheckoutSteps, type CheckoutStep } from "@/components/checkout/CheckoutSteps";
import { DeliveryForm, type DeliveryFormData } from "@/components/checkout/DeliveryForm";
import { PaymentOptions } from "@/components/checkout/PaymentOptions";
import { OrderConfirmation } from "@/components/checkout/OrderConfirmation";
import { CartSummary } from "@/components/cart/CartSummary";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { allItemsInstallmentEligible } from "@/lib/installment";
import type { Order, OrderItem } from "@shared/schema";

export default function Checkout() {
  const [, navigate] = useLocation();
  const { items, totalAmount, clearCart } = useCart();
  const { toast } = useToast();

  const [currentStep, setCurrentStep] = useState<CheckoutStep>("delivery");
  const [deliveryData, setDeliveryData] = useState<DeliveryFormData | null>(null);
  const [paymentPlan, setPaymentPlan] = useState<"full" | "installment">("full");
  const [order, setOrder] = useState<Order | null>(null);

  const deliveryFee = totalAmount >= 150000 ? 0 : 5000;
  const finalTotal = totalAmount + deliveryFee;

  const cartItems = items.map((item) => ({ category: item.product.category }));
  const installmentAvailable = allItemsInstallmentEligible(cartItems);

  useEffect(() => {
    if (!installmentAvailable && paymentPlan === "installment") {
      setPaymentPlan("full");
    }
  }, [installmentAvailable, paymentPlan]);

  const createOrderMutation = useMutation({
    mutationFn: async () => {
      if (!deliveryData) throw new Error("No delivery data");

      const orderItems: OrderItem[] = items.map((item) => ({
        productId: item.productId,
        productName: item.product.name,
        price: item.product.price,
        quantity: item.quantity,
        image: item.product.images[0] || "",
      }));

      const firstPayment = Math.round(finalTotal / 2);

      const orderData = {
        customerId: "guest",
        addressId: "new",
        items: JSON.stringify(orderItems),
        totalAmount: finalTotal,
        paymentPlan,
        firstPayment: paymentPlan === "installment" ? firstPayment : finalTotal,
        secondPayment: paymentPlan === "installment" ? finalTotal - firstPayment : 0,
        orderDate: new Date().toISOString(),
        customerEmail: deliveryData.email,
        deliveryAddress: {
          firstName: deliveryData.firstName,
          lastName: deliveryData.lastName,
          phone: deliveryData.phone,
          state: deliveryData.state,
          lga: deliveryData.lga,
          city: deliveryData.city,
          street: deliveryData.street,
          landmark: deliveryData.landmark,
        },
      };

      const response = await apiRequest("POST", "/api/orders", orderData);
      return response.json();
    },
    onSuccess: (data) => {
      setOrder(data);
      setCurrentStep("confirmation");
      clearCart();
      toast({
        title: "Order placed successfully!",
        description: "Check your email for order details.",
      });
    },
    onError: () => {
      toast({
        title: "Failed to place order",
        description: "Please try again or contact support.",
        variant: "destructive",
      });
    },
  });

  if (items.length === 0 && !order) {
    navigate("/cart");
    return null;
  }

  const handleDeliverySubmit = (data: DeliveryFormData) => {
    setDeliveryData(data);
    setCurrentStep("payment");
  };

  const handlePlaceOrder = () => {
    createOrderMutation.mutate();
  };

  const handleBack = () => {
    if (currentStep === "payment") {
      setCurrentStep("delivery");
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <CheckoutSteps currentStep={currentStep} />

      {currentStep === "confirmation" && order ? (
        <OrderConfirmation order={order} customerEmail={deliveryData?.email || ""} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            {currentStep === "payment" && (
              <Button
                variant="ghost"
                className="mb-4"
                onClick={handleBack}
                data-testid="button-back-delivery"
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Back to Delivery
              </Button>
            )}

            {currentStep === "delivery" && (
              <DeliveryForm onSubmit={handleDeliverySubmit} defaultValues={deliveryData || undefined} />
            )}

            {currentStep === "payment" && (
              <PaymentOptions
                totalAmount={finalTotal}
                paymentPlan={paymentPlan}
                onPaymentPlanChange={setPaymentPlan}
                onPlaceOrder={handlePlaceOrder}
                isLoading={createOrderMutation.isPending}
                installmentAvailable={installmentAvailable}
              />
            )}
          </div>

          <div className="lg:sticky lg:top-24 h-fit">
            <CartSummary showInstallmentOption paymentPlan={paymentPlan} />
          </div>
        </div>
      )}
    </main>
  );
}
