import { Link } from "wouter";
import { useWishlist } from "@/lib/wishlist";
import { useCart } from "@/lib/cart";
import { ProductGrid } from "@/components/product/ProductGrid";
import { Button } from "@/components/ui/button";
import { Heart, ArrowRight, ShoppingCart, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Wishlist() {
  const { items, clearWishlist } = useWishlist();
  const { addItem } = useCart();
  const { toast } = useToast();

  const handleAddAllToCart = () => {
    items.forEach((product) => {
      if (product.inStock) {
        addItem(product);
      }
    });
    toast({
      title: "Added to cart",
      description: `${items.filter((p) => p.inStock).length} items added to cart.`,
    });
  };

  if (items.length === 0) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center max-w-md mx-auto">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-muted mb-6">
            <Heart className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="font-serif text-2xl font-bold mb-4">Your Wishlist is Empty</h1>
          <p className="text-muted-foreground mb-8">
            Save items you love by clicking the heart icon on products. They'll appear here!
          </p>
          <Link href="/shop">
            <Button size="lg" data-testid="button-browse-products">
              Browse Products
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between gap-4 flex-wrap mb-8">
        <div>
          <h1 className="font-serif text-3xl font-bold">My Wishlist</h1>
          <p className="text-muted-foreground">{items.length} saved items</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleAddAllToCart}
            data-testid="button-add-all-cart"
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            Add All to Cart
          </Button>
          <Button
            variant="ghost"
            className="text-muted-foreground"
            onClick={clearWishlist}
            data-testid="button-clear-wishlist"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <ProductGrid products={items} />
    </main>
  );
}
