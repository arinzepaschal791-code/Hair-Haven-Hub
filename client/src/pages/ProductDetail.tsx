import { useState } from "react";
import { useRoute, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { InstallmentCalculator } from "@/components/product/InstallmentCalculator";
import { ProductGrid } from "@/components/product/ProductGrid";
import { useCart } from "@/lib/cart";
import { useWishlist } from "@/lib/wishlist";
import { useToast } from "@/hooks/use-toast";
import {
  ShoppingCart,
  Minus,
  Plus,
  Truck,
  Shield,
  RefreshCw,
  ChevronLeft,
  Star,
  Heart,
} from "lucide-react";
import type { Product } from "@shared/schema";

export default function ProductDetail() {
  const [, params] = useRoute("/product/:id");
  const productId = params?.id;
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const { addItem } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const { toast } = useToast();

  const { data: product, isLoading } = useQuery<Product>({
    queryKey: ["/api/products", productId],
    enabled: !!productId,
  });

  const { data: relatedProducts = [] } = useQuery<Product[]>({
    queryKey: ["/api/products"],
  });

  const filteredRelated = relatedProducts
    .filter((p) => p.id !== productId && p.category === product?.category)
    .slice(0, 4);

  const isWishlisted = product ? isInWishlist(product.id) : false;

  const handleAddToCart = () => {
    if (!product) return;
    addItem(product, quantity);
    toast({
      title: "Added to cart",
      description: `${quantity}x ${product.name} has been added to your cart.`,
    });
  };

  const handleToggleWishlist = () => {
    if (!product) return;
    toggleWishlist(product);
    toast({
      title: isWishlisted ? "Removed from wishlist" : "Added to wishlist",
      description: isWishlisted
        ? `${product.name} has been removed from your wishlist.`
        : `${product.name} has been added to your wishlist.`,
    });
  };

  if (isLoading) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Skeleton className="aspect-square rounded-md" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </main>
    );
  }

  if (!product) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">Product Not Found</h1>
        <Link href="/shop">
          <Button>Back to Shop</Button>
        </Link>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <Link href="/shop">
        <Button variant="ghost" className="mb-6" data-testid="button-back-shop">
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Shop
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
        <div className="space-y-4">
          <div className="aspect-square overflow-hidden rounded-md bg-muted relative">
            <img
              src={product.images[selectedImage] || "/placeholder.jpg"}
              alt={product.name}
              className="w-full h-full object-cover"
            />
            <Button
              size="icon"
              variant="secondary"
              className="absolute top-4 right-4 bg-background/80 backdrop-blur"
              onClick={handleToggleWishlist}
              data-testid="button-wishlist"
            >
              <Heart className={`h-5 w-5 ${isWishlisted ? "fill-red-500 text-red-500" : ""}`} />
            </Button>
          </div>
          {product.images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {product.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`shrink-0 w-20 h-20 rounded-md overflow-hidden border-2 transition-colors ${
                    selectedImage === idx
                      ? "border-primary"
                      : "border-transparent"
                  }`}
                  data-testid={`button-thumbnail-${idx}`}
                >
                  <img
                    src={img}
                    alt={`${product.name} ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-muted-foreground uppercase tracking-wide">
              {product.category.replace("-", " ")}
            </span>
            {product.badge && (
              <Badge variant={product.badge === "Sale" ? "destructive" : "default"}>
                {product.badge}
              </Badge>
            )}
          </div>

          <h1 className="font-serif text-3xl font-bold mb-4">{product.name}</h1>

          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={`h-4 w-4 ${
                    i < 4 ? "text-yellow-500 fill-yellow-500" : "text-muted"
                  }`}
                />
              ))}
            </div>
            <span className="text-sm text-muted-foreground">(24 reviews)</span>
          </div>

          <div className="mb-6">
            <span className="font-bold text-3xl">
              N{product.price.toLocaleString()}
            </span>
            <p className="text-sm text-primary font-medium mt-1">
              or N{Math.round(product.price / 2).toLocaleString()} x 2 installments
            </p>
          </div>

          {product.length && (
            <p className="text-sm mb-2">
              <span className="text-muted-foreground">Length:</span>{" "}
              <span className="font-medium">{product.length}</span>
            </p>
          )}

          {product.texture && (
            <p className="text-sm mb-4">
              <span className="text-muted-foreground">Texture:</span>{" "}
              <span className="font-medium capitalize">{product.texture}</span>
            </p>
          )}

          <div className="flex items-center gap-4 mb-6">
            <span className="text-sm text-muted-foreground">Quantity:</span>
            <div className="flex items-center gap-2">
              <Button
                size="icon"
                variant="outline"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                disabled={quantity <= 1}
                data-testid="button-decrease-qty"
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-12 text-center font-medium">{quantity}</span>
              <Button
                size="icon"
                variant="outline"
                onClick={() => setQuantity((q) => q + 1)}
                data-testid="button-increase-qty"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="space-y-3 mb-8">
            <Button
              className="w-full"
              size="lg"
              onClick={handleAddToCart}
              disabled={!product.inStock}
              data-testid="button-add-to-cart"
            >
              <ShoppingCart className="h-5 w-5 mr-2" />
              {product.inStock ? "Add to Cart" : "Out of Stock"}
            </Button>
            <Link href="/cart">
              <Button variant="outline" className="w-full" size="lg" data-testid="button-buy-now">
                Buy Now
              </Button>
            </Link>
          </div>

          <InstallmentCalculator price={product.price} quantity={quantity} />

          <div className="mt-6 space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <Truck className="h-5 w-5 text-primary" />
              <span>Free delivery on orders above N150,000</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Shield className="h-5 w-5 text-primary" />
              <span>100% Authentic guarantee</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <RefreshCw className="h-5 w-5 text-primary" />
              <span>7-day return policy</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-12">
        <Tabs defaultValue="description" className="w-full">
          <TabsList>
            <TabsTrigger value="description" data-testid="tab-description">Description</TabsTrigger>
            <TabsTrigger value="specs" data-testid="tab-specs">Specifications</TabsTrigger>
            <TabsTrigger value="care" data-testid="tab-care">Care Instructions</TabsTrigger>
          </TabsList>
          <TabsContent value="description" className="mt-4">
            <p className="text-muted-foreground leading-relaxed">
              {product.description}
            </p>
          </TabsContent>
          <TabsContent value="specs" className="mt-4">
            <div className="space-y-2">
              <p><span className="font-medium">Category:</span> {product.category.replace("-", " ")}</p>
              {product.length && <p><span className="font-medium">Length:</span> {product.length}</p>}
              {product.texture && <p><span className="font-medium">Texture:</span> {product.texture}</p>}
              <p><span className="font-medium">Material:</span> 100% Human Hair</p>
              <p><span className="font-medium">Origin:</span> Imported</p>
            </div>
          </TabsContent>
          <TabsContent value="care" className="mt-4">
            <ul className="list-disc list-inside space-y-2 text-muted-foreground">
              <li>Wash with sulfate-free shampoo</li>
              <li>Use a wide-tooth comb to detangle</li>
              <li>Air dry or use low heat settings</li>
              <li>Store in a silk or satin bag when not in use</li>
              <li>Deep condition weekly for best results</li>
            </ul>
          </TabsContent>
        </Tabs>
      </div>

      {filteredRelated.length > 0 && (
        <section className="mt-16">
          <h2 className="font-serif text-2xl font-bold mb-6">Related Products</h2>
          <ProductGrid products={filteredRelated} />
        </section>
      )}
    </main>
  );
}
