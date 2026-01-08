import { Link } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import boneImage from "@assets/stock_images/woman_long_straight__eee03e54.jpg";
import wigImage from "@assets/stock_images/beautiful_african_wo_7f5bcd22.jpg";
import careImage from "@assets/stock_images/hair_care_products_b_dceab05b.jpg";

const collections = [
  {
    id: "bone-straight",
    title: "Bone Straight",
    description: "Silky smooth, sleek perfection",
    image: boneImage,
    href: "/bone-straight",
  },
  {
    id: "wigs",
    title: "Luxury Wigs",
    description: "Ready-to-wear glamour",
    image: wigImage,
    href: "/wigs",
  },
  {
    id: "hair-care",
    title: "Hair Care",
    description: "Maintain your crown",
    image: careImage,
    href: "/shop",
  },
];

export function FeaturedCollections() {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="font-serif text-3xl md:text-4xl font-bold mb-4">
            Shop by Collection
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Find your perfect match from our curated collections of premium hair products
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {collections.map((collection) => (
            <Link key={collection.id} href={collection.href}>
              <Card className="group cursor-pointer overflow-hidden border-0 bg-card hover-elevate" data-testid={`card-collection-${collection.id}`}>
                <CardContent className="p-0">
                  <div className="relative aspect-[4/5] overflow-hidden">
                    <img
                      src={collection.image}
                      alt={collection.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                    <div className="absolute bottom-0 left-0 right-0 p-6">
                      <h3 className="font-serif text-2xl font-bold text-white mb-2">
                        {collection.title}
                      </h3>
                      <p className="text-white/80 mb-4">
                        {collection.description}
                      </p>
                      <Button variant="secondary" size="sm" className="group/btn">
                        Shop Now
                        <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover/btn:translate-x-1" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
