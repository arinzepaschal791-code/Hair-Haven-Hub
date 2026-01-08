import { Button } from "@/components/ui/button";
import { Minus, Plus, Trash2 } from "lucide-react";
import { useCart } from "@/lib/cart";
import type { CartItemWithProduct } from "@shared/schema";

interface CartItemProps {
  item: CartItemWithProduct;
}

export function CartItem({ item }: CartItemProps) {
  const { updateQuantity, removeItem } = useCart();

  return (
    <div className="flex gap-4 py-4 border-b last:border-b-0" data-testid={`cart-item-${item.productId}`}>
      <div className="w-20 h-20 rounded-md overflow-hidden shrink-0">
        <img
          src={item.product.images[0] || "/placeholder.jpg"}
          alt={item.product.name}
          className="w-full h-full object-cover"
        />
      </div>

      <div className="flex-1 min-w-0">
        <h4 className="font-medium truncate">{item.product.name}</h4>
        <p className="text-sm text-muted-foreground mb-2">
          {item.product.category}
          {item.product.length && ` - ${item.product.length}`}
        </p>
        <p className="font-bold">N{item.product.price.toLocaleString()}</p>
      </div>

      <div className="flex flex-col items-end justify-between">
        <Button
          size="icon"
          variant="ghost"
          className="h-8 w-8 text-muted-foreground hover:text-destructive"
          onClick={() => removeItem(item.productId)}
          data-testid={`button-remove-${item.productId}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>

        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="outline"
            className="h-7 w-7"
            onClick={() => updateQuantity(item.productId, item.quantity - 1)}
            data-testid={`button-decrease-${item.productId}`}
          >
            <Minus className="h-3 w-3" />
          </Button>
          <span className="w-8 text-center text-sm font-medium">
            {item.quantity}
          </span>
          <Button
            size="icon"
            variant="outline"
            className="h-7 w-7"
            onClick={() => updateQuantity(item.productId, item.quantity + 1)}
            data-testid={`button-increase-${item.productId}`}
          >
            <Plus className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}
