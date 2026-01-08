import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CreditCard, Wallet, Calendar, Check, Building } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

interface PaymentOptionsProps {
  totalAmount: number;
  paymentPlan: "full" | "installment";
  onPaymentPlanChange: (plan: "full" | "installment") => void;
  onPlaceOrder: () => void;
  isLoading?: boolean;
}

export function PaymentOptions({
  totalAmount,
  paymentPlan,
  onPaymentPlanChange,
  onPlaceOrder,
  isLoading = false,
}: PaymentOptionsProps) {
  const firstPayment = Math.round(totalAmount / 2);
  const secondPayment = totalAmount - firstPayment;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Choose Payment Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={paymentPlan}
            onValueChange={(value: "full" | "installment") =>
              onPaymentPlanChange(value)
            }
            className="space-y-4"
          >
            <div
              className={`flex items-start gap-4 p-4 rounded-md border-2 cursor-pointer transition-colors ${
                paymentPlan === "full"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => onPaymentPlanChange("full")}
            >
              <RadioGroupItem value="full" id="full" className="mt-1" data-testid="radio-full-payment" />
              <div className="flex-1">
                <Label
                  htmlFor="full"
                  className="text-base font-medium cursor-pointer flex items-center gap-2"
                >
                  <Wallet className="h-5 w-5" />
                  Pay in Full
                </Label>
                <p className="text-sm text-muted-foreground mt-1">
                  Pay the complete amount now
                </p>
                <p className="font-bold text-lg mt-2">
                  N{totalAmount.toLocaleString()}
                </p>
              </div>
            </div>

            <div
              className={`flex items-start gap-4 p-4 rounded-md border-2 cursor-pointer transition-colors ${
                paymentPlan === "installment"
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => onPaymentPlanChange("installment")}
            >
              <RadioGroupItem value="installment" id="installment" className="mt-1" data-testid="radio-installment" />
              <div className="flex-1">
                <Label
                  htmlFor="installment"
                  className="text-base font-medium cursor-pointer flex items-center gap-2"
                >
                  <Calendar className="h-5 w-5" />
                  Pay in 2 Installments
                  <Badge variant="secondary" className="ml-2">Popular</Badge>
                </Label>
                <p className="text-sm text-muted-foreground mt-1">
                  Split your payment over 30 days
                </p>
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      Pay today (50%)
                    </span>
                    <span className="font-bold text-primary">
                      N{firstPayment.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Pay within 30 days
                    </span>
                    <span>N{secondPayment.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payment Methods</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            After placing your order, you can pay via:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
              <Building className="h-5 w-5 text-primary" />
              <span className="text-sm">Bank Transfer</span>
            </div>
            <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
              <CreditCard className="h-5 w-5 text-primary" />
              <span className="text-sm">Card Payment</span>
            </div>
            <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
              <SiWhatsapp className="h-5 w-5 text-[#25D366]" />
              <span className="text-sm">WhatsApp Pay</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button
        className="w-full"
        size="lg"
        onClick={onPlaceOrder}
        disabled={isLoading}
        data-testid="button-place-order"
      >
        {isLoading ? "Processing..." : `Place Order - N${
          paymentPlan === "full"
            ? totalAmount.toLocaleString()
            : firstPayment.toLocaleString()
        }`}
      </Button>
    </div>
  );
}
