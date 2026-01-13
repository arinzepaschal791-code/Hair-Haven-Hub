import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CreditCard, Calendar, Check } from "lucide-react";

interface InstallmentCalculatorProps {
  price: number;
  quantity?: number;
}

export function InstallmentCalculator({ price, quantity = 1 }: InstallmentCalculatorProps) {
  const totalPrice = price * quantity;
  const firstPayment = Math.round(totalPrice / 2);
  const secondPayment = totalPrice - firstPayment;

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          Installment Payment Available
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-primary/10 rounded-md">
            <div className="flex items-center gap-2">
              <div className="rounded-full bg-primary p-1">
                <Check className="h-3 w-3 text-primary-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium">First Payment</p>
                <p className="text-xs text-muted-foreground">Pay today</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold">N{firstPayment.toLocaleString()}</p>
              <Badge variant="secondary" className="text-xs">50%</Badge>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-muted rounded-md">
            <div className="flex items-center gap-2">
              <div className="rounded-full bg-muted-foreground/20 p-1">
                <Calendar className="h-3 w-3 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium">Second Payment</p>
                <p className="text-xs text-muted-foreground">Within 30 days</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold">N{secondPayment.toLocaleString()}</p>
              <Badge variant="outline" className="text-xs">50%</Badge>
            </div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Your order ships after complete payment is received.
        </p>
      </CardContent>
    </Card>
  );
}
