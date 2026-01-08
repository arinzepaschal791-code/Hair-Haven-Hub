import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { ProductGrid } from "@/components/product/ProductGrid";
import { QuickViewModal } from "@/components/product/QuickViewModal";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SlidersHorizontal } from "lucide-react";
import type { Product } from "@shared/schema";

interface CategoryPageProps {
  category: string;
  title: string;
  description: string;
}

export default function CategoryPage({ category, title, description }: CategoryPageProps) {
  const [sortBy, setSortBy] = useState("newest");
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);

  const { data: products = [], isLoading } = useQuery<Product[]>({
    queryKey: ["/api/products"],
  });

  const filteredProducts = useMemo(() => {
    let result = products.filter((p) => p.category === category);

    switch (sortBy) {
      case "price-asc":
        result.sort((a, b) => a.price - b.price);
        break;
      case "price-desc":
        result.sort((a, b) => b.price - a.price);
        break;
      case "name":
        result.sort((a, b) => a.name.localeCompare(b.name));
        break;
      default:
        break;
    }

    return result;
  }, [products, category, sortBy]);

  return (
    <main className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="font-serif text-3xl md:text-4xl font-bold mb-2">{title}</h1>
          <p className="text-muted-foreground">{description}</p>
        </div>

        <div className="flex items-center justify-between gap-4 mb-6">
          <p className="text-sm text-muted-foreground">
            {filteredProducts.length} products
          </p>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40" data-testid="select-sort-category">
              <SlidersHorizontal className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="price-asc">Price: Low to High</SelectItem>
              <SelectItem value="price-desc">Price: High to Low</SelectItem>
              <SelectItem value="name">Name</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <ProductGrid
          products={filteredProducts}
          isLoading={isLoading}
          onQuickView={setQuickViewProduct}
        />

        {!isLoading && filteredProducts.length === 0 && (
          <div className="text-center py-16">
            <p className="text-muted-foreground text-lg mb-4">
              No products in this category yet.
            </p>
            <Button variant="outline">Check back soon!</Button>
          </div>
        )}
      </div>

      <QuickViewModal
        product={quickViewProduct}
        isOpen={!!quickViewProduct}
        onClose={() => setQuickViewProduct(null)}
      />
    </main>
  );
}
