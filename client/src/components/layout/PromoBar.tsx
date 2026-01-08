import { X, Truck, CreditCard } from "lucide-react";
import { useState } from "react";

export function PromoBar() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="bg-primary text-primary-foreground py-2 px-4 relative">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-sm">
        <div className="flex items-center gap-6 flex-wrap justify-center">
          <span className="flex items-center gap-2">
            <Truck className="h-4 w-4" />
            Free delivery on orders above N150,000
          </span>
          <span className="hidden md:flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Pay in 2 easy installments!
          </span>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="absolute right-4 top-1/2 -translate-y-1/2 opacity-70 hover:opacity-100 transition-opacity"
          data-testid="button-close-promo"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
