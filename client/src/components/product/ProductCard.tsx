import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart, Eye, Heart } from "lucide-react";
import { useCart } from "@/lib/cart";
import { useWishlist } from "@/lib/wishlist";
import { useToast } from "@/hooks/use-toast";
import type { Product } from "@shared/schema";
import { Link } from "wouter";

interface ProductCardProps {
  product: Product;
  onQuickView?: (product: Product) => void;
}

export function ProductCard({ product, onQuickView }: ProductCardProps) {
  const { addItem } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const { toast } = useToast();
  const isWishlisted = isInWishlist(product.id);

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    addItem(product);
    toast({
      title: "Added to cart",
      description: `${product.name} has been added to your cart.`,
    });
  };

  const handleQuickView = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onQuickView?.(product);
  };

  const handleWishlist = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleWishlist(product);
    toast({
      title: isWishlisted ? "Removed from wishlist" : "Added to wishlist",
      description: isWishlisted
        ? `${product.name} has been removed from your wishlist.`
        : `${product.name} has been added to your wishlist.`,
    });
  };

  const installmentAmount = Math.round(product.price / 2);
  const lowStock = product.stockCount && product.stockCount <= 3;

  return (
    <Link href={`/product/${product.id}`}>
      <Card
        className="group cursor-pointer overflow-visible hover-elevate"
        data-testid={`card-product-${product.id}`}
      >
        <CardContent className="p-0">
          <div className="relative aspect-square overflow-hidden rounded-t-md">
            <img
              src={product.images[0] || "/placeholder.jpg"}
              alt={product.name}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            
            <div className="absolute top-3 left-3 flex flex-col gap-2">
              {product.badge && (
                <Badge variant={product.badge === "Sale" ? "destructive" : "default"} className="text-xs">
                  {product.badge}
                </Badge>
              )}
              {lowStock && (
                <Badge variant="secondary" className="text-xs bg-orange-500/90 text-white">
                  Only {product.stockCount} left
                </Badge>
              )}
            </div>

            <div className="absolute top-3 right-3 flex flex-col gap-2">
              <Button
                size="icon"
                variant="secondary"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity bg-background/80 backdrop-blur"
                onClick={handleWishlist}
                data-testid={`button-wishlist-${product.id}`}
              >
                <Heart className={`h-4 w-4 ${isWishlisted ? "fill-red-500 text-red-500" : ""}`} />
              </Button>
              {onQuickView && (
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity bg-background/80 backdrop-blur"
                  onClick={handleQuickView}
                  data-testid={`button-quickview-${product.id}`}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              )}
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                size="sm"
                className="w-full"
                onClick={handleAddToCart}
                disabled={!product.inStock}
                data-testid={`button-add-cart-${product.id}`}
              >
                <ShoppingCart className="h-4 w-4 mr-2" />
                {product.inStock ? "Add to Cart" : "Out of Stock"}
              </Button>
            </div>
          </div>

          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">
              {product.category.replace("-", " ")}
            </p>
            <h3 className="font-medium mb-2 line-clamp-2">{product.name}</h3>
            
            <div className="flex items-baseline gap-2 mb-2">
              <span className="font-bold text-lg">
                N{product.price.toLocaleString()}
              </span>
            </div>

            <p className="text-xs text-primary font-medium">
              or N{installmentAmount.toLocaleString()} x 2 installments
            </p>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
