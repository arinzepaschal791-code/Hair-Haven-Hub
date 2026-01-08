import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart, Minus, Plus, CreditCard } from "lucide-react";
import { useCart } from "@/lib/cart";
import { useToast } from "@/hooks/use-toast";
import { Link } from "wouter";
import type { Product } from "@shared/schema";

interface QuickViewModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
}

export function QuickViewModal({ product, isOpen, onClose }: QuickViewModalProps) {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useCart();
  const { toast } = useToast();

  if (!product) return null;

  const handleAddToCart = () => {
    addItem(product, quantity);
    toast({
      title: "Added to cart",
      description: `${quantity}x ${product.name} has been added to your cart.`,
    });
    onClose();
    setQuantity(1);
  };

  const installmentAmount = Math.round(product.price / 2);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="sr-only">Quick View: {product.name}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="aspect-square overflow-hidden rounded-md">
            <img
              src={product.images[0] || "/placeholder.jpg"}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">
                {product.category}
              </span>
              {product.badge && (
                <Badge variant={product.badge === "Sale" ? "destructive" : "default"}>
                  {product.badge}
                </Badge>
              )}
            </div>

            <h2 className="font-serif text-2xl font-bold mb-4">{product.name}</h2>

            <div className="mb-4">
              <span className="font-bold text-2xl">
                N{product.price.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center gap-2 mb-6 p-3 bg-primary/10 rounded-md">
              <CreditCard className="h-4 w-4 text-primary" />
              <span className="text-sm">
                Pay N{installmentAmount.toLocaleString()} x 2 installments
              </span>
            </div>

            <p className="text-muted-foreground mb-6 line-clamp-3">
              {product.description}
            </p>

            {product.length && (
              <p className="text-sm mb-2">
                <span className="text-muted-foreground">Length:</span>{" "}
                <span className="font-medium">{product.length}</span>
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
                  data-testid="button-decrease-quantity"
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-12 text-center font-medium">{quantity}</span>
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => setQuantity((q) => q + 1)}
                  data-testid="button-increase-quantity"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="mt-auto space-y-3">
              <Button
                className="w-full"
                size="lg"
                onClick={handleAddToCart}
                disabled={!product.inStock}
                data-testid="button-quickview-add-cart"
              >
                <ShoppingCart className="h-5 w-5 mr-2" />
                {product.inStock ? "Add to Cart" : "Out of Stock"}
              </Button>

              <Link href={`/product/${product.id}`}>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={onClose}
                  data-testid="button-view-details"
                >
                  View Full Details
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
