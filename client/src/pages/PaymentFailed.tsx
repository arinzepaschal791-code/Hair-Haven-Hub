import { Link, useSearch } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { XCircle, RefreshCw, Home, MessageCircle } from "lucide-react";

export default function PaymentFailed() {
  const searchString = useSearch();
  const params = new URLSearchParams(searchString);
  const reference = params.get("reference");

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-4 w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <XCircle className="h-12 w-12 text-red-600" />
          </div>
          <CardTitle className="font-serif text-2xl text-red-600">
            Payment Failed
          </CardTitle>
          <CardDescription className="text-base">
            We couldn't process your payment. Please try again.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {reference && (
            <div className="p-4 bg-muted rounded-md">
              <p className="text-sm text-muted-foreground">Transaction Reference</p>
              <p className="font-mono text-sm">{reference}</p>
            </div>
          )}

          <div className="p-4 bg-destructive/10 rounded-md text-left">
            <p className="text-sm font-medium mb-2">Common reasons for payment failure:</p>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Insufficient funds in your account</li>
              <li>Card declined by your bank</li>
              <li>Network connection issues</li>
              <li>Transaction timeout</li>
            </ul>
          </div>

          <div className="flex flex-col gap-3 pt-4">
            <Link href="/shop">
              <Button className="w-full" data-testid="button-try-again">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </Link>
            <a
              href="https://wa.me/2348012345678"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" className="w-full" data-testid="button-contact-support">
                <MessageCircle className="h-4 w-4 mr-2" />
                Contact Support on WhatsApp
              </Button>
            </a>
            <Link href="/">
              <Button variant="ghost" className="w-full" data-testid="button-go-home">
                <Home className="h-4 w-4 mr-2" />
                Back to Home
              </Button>
            </Link>
          </div>

          <p className="text-xs text-muted-foreground pt-4">
            If money was deducted from your account, please contact us immediately.
            We will verify and resolve within 24 hours.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
