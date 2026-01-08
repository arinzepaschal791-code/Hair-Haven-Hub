import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Mail, Gift, Check } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import { useToast } from "@/hooks/use-toast";

export function Newsletter() {
  const [email, setEmail] = useState("");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const { toast } = useToast();

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    
    setIsSubscribed(true);
    toast({
      title: "Welcome to GlowHair!",
      description: "You've been subscribed to our newsletter. Check your email for 10% off!",
    });
    setEmail("");
  };

  return (
    <section className="py-16 md:py-24 bg-primary">
      <div className="max-w-7xl mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 mb-6">
            <Gift className="h-8 w-8 text-white" />
          </div>
          
          <h2 className="font-serif text-3xl md:text-4xl font-bold text-white mb-4">
            Get 10% Off Your First Order
          </h2>
          <p className="text-white/80 text-lg mb-8">
            Subscribe to our newsletter and be the first to know about new arrivals, exclusive deals, and hair care tips.
          </p>

          {isSubscribed ? (
            <Card className="bg-white/10 border-white/20">
              <CardContent className="p-6 flex items-center justify-center gap-3">
                <div className="rounded-full bg-green-500 p-1">
                  <Check className="h-4 w-4 text-white" />
                </div>
                <p className="text-white font-medium">
                  You're subscribed! Check your email for your discount code.
                </p>
              </CardContent>
            </Card>
          ) : (
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto mb-8">
              <div className="relative flex-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 h-12 bg-white"
                  required
                  data-testid="input-newsletter-email"
                />
              </div>
              <Button type="submit" size="lg" variant="secondary" className="h-12" data-testid="button-subscribe">
                Subscribe
              </Button>
            </form>
          )}

          <div className="flex items-center justify-center gap-4 mt-8">
            <span className="text-white/60 text-sm">Or chat with us on</span>
            <a
              href="https://wa.me/2348012345678"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-white font-medium hover:underline"
              data-testid="link-newsletter-whatsapp"
            >
              <SiWhatsapp className="h-5 w-5" />
              WhatsApp
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
