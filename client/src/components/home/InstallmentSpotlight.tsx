import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditCard, Calendar, Shield, Check } from "lucide-react";
import { Link } from "wouter";

export function InstallmentSpotlight() {
  const examplePrice = 120000;
  const firstPayment = examplePrice / 2;

  return (
    <section className="py-16 md:py-24 bg-card">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <Badge variant="secondary" className="mb-4">
              <CreditCard className="h-3 w-3 mr-1" />
              Flexible Payment
            </Badge>
            <h2 className="font-serif text-3xl md:text-4xl font-bold mb-6">
              Buy Now, Pay in <span className="text-primary">2 Easy Installments</span>
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              We understand that quality hair is an investment. That's why we offer flexible payment plans on our <span className="font-medium text-foreground">Wigs and Bone Straight Hair</span> that let you split your purchase into two easy payments. Your order ships once payment is complete!
            </p>

            <div className="space-y-4 mb-8">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary/10 p-2">
                  <Check className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="font-medium">Pay 50% upfront</p>
                  <p className="text-sm text-muted-foreground">
                    Reserve your order with the first payment
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary/10 p-2">
                  <Calendar className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="font-medium">Pay remaining 50% within 30 days</p>
                  <p className="text-sm text-muted-foreground">
                    Flexible timeline that works for you
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary/10 p-2">
                  <Shield className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="font-medium">No hidden fees</p>
                  <p className="text-sm text-muted-foreground">
                    Same price whether you pay full or in installments
                  </p>
                </div>
              </div>
            </div>

            <Link href="/shop">
              <Button size="lg" data-testid="button-installment-shop">
                Start Shopping
              </Button>
            </Link>
          </div>

          <div>
            <Card className="bg-background border-2 border-primary/20">
              <CardContent className="p-8">
                <div className="text-center mb-6">
                  <p className="text-muted-foreground mb-2">Example: Bone Straight 22"</p>
                  <p className="font-serif text-4xl font-bold">
                    N{examplePrice.toLocaleString()}
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary/10 rounded-md">
                    <div>
                      <p className="text-sm text-muted-foreground">First Payment (Today)</p>
                      <p className="font-bold text-xl">N{firstPayment.toLocaleString()}</p>
                    </div>
                    <Badge variant="default">50%</Badge>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-muted rounded-md">
                    <div>
                      <p className="text-sm text-muted-foreground">Second Payment (Within 30 days)</p>
                      <p className="font-bold text-xl">N{firstPayment.toLocaleString()}</p>
                    </div>
                    <Badge variant="secondary">50%</Badge>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t text-center">
                  <p className="text-sm text-muted-foreground">
                    Order ships once full payment is complete!
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
