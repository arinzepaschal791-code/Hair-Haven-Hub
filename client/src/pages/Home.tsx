import { Hero } from "@/components/home/Hero";
import { FeaturedCollections } from "@/components/home/FeaturedCollections";
import { InstallmentSpotlight } from "@/components/home/InstallmentSpotlight";
import { WhyChooseUs } from "@/components/home/WhyChooseUs";
import { Testimonials } from "@/components/home/Testimonials";
import { Newsletter } from "@/components/home/Newsletter";
import { ProductGrid } from "@/components/product/ProductGrid";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import type { Product } from "@shared/schema";

export default function Home() {
  const { data: products = [], isLoading } = useQuery<Product[]>({
    queryKey: ["/api/products"],
  });

  const featuredProducts = products.filter((p) => p.featured).slice(0, 4);

  return (
    <main>
      <Hero />
      <FeaturedCollections />

      <section className="py-16 md:py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-serif text-3xl md:text-4xl font-bold mb-2">
                Featured Products
              </h2>
              <p className="text-muted-foreground">
                Our most popular hair pieces loved by customers
              </p>
            </div>
            <Link href="/shop">
              <Button variant="outline" className="hidden md:flex" data-testid="button-view-all-products">
                View All
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>

          <ProductGrid products={featuredProducts} isLoading={isLoading} />

          <div className="mt-8 text-center md:hidden">
            <Link href="/shop">
              <Button data-testid="button-view-all-products-mobile">
                View All Products
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <InstallmentSpotlight />
      <WhyChooseUs />
      <Testimonials />
      <Newsletter />
    </main>
  );
}
