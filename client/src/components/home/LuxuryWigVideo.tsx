import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Crown, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import wigVideo from "@assets/nora6_1768080185424.mp4";

export function LuxuryWigVideo() {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="relative aspect-[9/16] lg:aspect-video rounded-lg overflow-hidden shadow-xl">
            <video
              autoPlay
              loop
              muted
              playsInline
              className="absolute inset-0 w-full h-full object-cover"
              data-testid="video-luxury-wig"
            >
              <source src={wigVideo} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          </div>

          <div className="lg:pl-8">
            <Badge variant="secondary" className="mb-4 bg-primary/10 border-primary/20">
              <Crown className="h-3 w-3 mr-1" />
              Premium Collection
            </Badge>
            <h2 className="font-serif text-3xl md:text-4xl font-bold mb-6">
              Luxury Wigs for the{" "}
              <span className="text-primary">Modern Queen</span>
            </h2>
            <p className="text-muted-foreground text-lg mb-6 leading-relaxed">
              Experience the ultimate in elegance with our hand-crafted luxury wigs. 
              Each piece is designed for comfort, durability, and that flawless 
              natural look you deserve.
            </p>
            
            <ul className="space-y-3 mb-8">
              <li className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-muted-foreground">100% Human Hair - Premium Grade</span>
              </li>
              <li className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-muted-foreground">Pre-plucked Hairline for Natural Look</span>
              </li>
              <li className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-muted-foreground">Breathable Cap Construction</span>
              </li>
              <li className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-muted-foreground">Easy Installment Payment Available</span>
              </li>
            </ul>

            <Link href="/wigs">
              <Button size="lg" data-testid="button-shop-wigs">
                Shop Luxury Wigs
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
