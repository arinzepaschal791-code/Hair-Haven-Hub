import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, Shield, Truck, Sparkles } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import { Link } from "wouter";
import aboutImage from "@assets/stock_images/hair_care_products_b_d3a302a2.jpg";

export default function About() {
  return (
    <main>
      <section className="relative py-20 bg-card">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="font-serif text-4xl md:text-5xl font-bold mb-6">
                About <span className="text-primary">NORA HAIR LINE</span>
              </h1>
              <p className="text-primary italic text-xl mb-4">Luxury for less...</p>
              <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
                NORA HAIR LINE is your trusted destination for premium imported hair products. 
                Located at Tradefair Shopping Center, Badagry Express Way, Lagos State, we bring you authentic, 
                high-quality Closure, Frontals, 360 Illusion Frontal, Wigs & Bundles 
                directly from top international suppliers.
              </p>
              <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
                We understand that hair is more than just an accessory - it's a statement of 
                confidence and self-expression. That's why we're committed to providing only the 
                best products at affordable prices that help Nigerian women look and feel their absolute best.
              </p>
              <Link href="/shop">
                <Button size="lg" data-testid="button-explore-collection">
                  Explore Our Collection
                </Button>
              </Link>
            </div>
            <div className="relative">
              <img
                src={aboutImage}
                alt="NORAHAIRLINE products"
                className="rounded-md shadow-lg"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="font-serif text-3xl font-bold mb-4">Our Values</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              What sets us apart from other hair vendors in Nigeria
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
                  <Sparkles className="h-7 w-7 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Authentic Quality</h3>
                <p className="text-sm text-muted-foreground">
                  100% human hair imported directly from trusted international suppliers
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
                  <Heart className="h-7 w-7 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Customer First</h3>
                <p className="text-sm text-muted-foreground">
                  We prioritize your satisfaction with flexible payment plans and expert support
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
                  <Shield className="h-7 w-7 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Trust & Transparency</h3>
                <p className="text-sm text-muted-foreground">
                  Same price for full or installment payment - no hidden fees ever
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
                  <Truck className="h-7 w-7 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Fast Delivery</h3>
                <p className="text-sm text-muted-foreground">
                  Same-day delivery in Lagos, nationwide delivery within 2-5 days
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24 bg-primary">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="font-serif text-3xl font-bold text-white mb-6">
            Have Questions? Let's Chat!
          </h2>
          <p className="text-white/80 text-lg mb-8">
            Our team is always ready to help you find the perfect hair for your needs. 
            Reach out to us on WhatsApp for personalized recommendations.
          </p>
          <a
            href="https://wa.me/2348038707795"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="lg" variant="secondary" data-testid="button-contact-whatsapp">
              <SiWhatsapp className="h-5 w-5 mr-2" />
              Chat on WhatsApp
            </Button>
          </a>
        </div>
      </section>
    </main>
  );
}
