import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, CreditCard } from "lucide-react";
import heroImage from "@assets/stock_images/woman_long_straight__87475d1c.jpg";

export function Hero() {
  return (
    <section className="relative min-h-[80vh] flex items-center overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/60 to-black/40" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 py-20">
        <div className="max-w-2xl">
          <Badge variant="secondary" className="mb-4 bg-primary/20 text-white border-primary/30">
            <Sparkles className="h-3 w-3 mr-1" />
            Authentic Import Quality
          </Badge>
          
          <h1 className="font-serif text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            Premium Hair.
            <br />
            <span className="text-primary">Perfect Confidence.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-white/80 mb-8 leading-relaxed">
            Discover our collection of authentic bone straight hair and luxury wigs. 
            Imported directly for Nigerian queens who demand nothing but the best.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <Link href="/shop">
              <Button size="lg" className="text-lg px-8" data-testid="button-hero-shop">
                Shop Collection
              </Button>
            </Link>
            <Link href="/shop">
              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8 bg-white/10 border-white/30 text-white hover:bg-white/20 backdrop-blur"
                data-testid="button-hero-installments"
              >
                <CreditCard className="h-5 w-5 mr-2" />
                Payment Plans Available
              </Button>
            </Link>
          </div>

          <div className="flex items-center gap-6 text-white/70 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400" />
              <span>100% Human Hair</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400" />
              <span>Fast Lagos Delivery</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
