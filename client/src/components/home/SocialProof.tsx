import { useState, useEffect } from "react";
import { ShoppingBag, X } from "lucide-react";

const recentPurchases = [
  { name: "Jane", location: "Lagos", product: "Bone Straight 22\"" },
  { name: "Chika", location: "Abuja", product: "Luxury Frontal Wig" },
  { name: "Ngozi", location: "Port Harcourt", product: "Bone Straight 18\"" },
  { name: "Funke", location: "Ibadan", product: "Body Wave 20\"" },
  { name: "Aisha", location: "Kano", product: "Closure Wig" },
];

export function SocialProof() {
  const [currentPurchase, setCurrentPurchase] = useState<typeof recentPurchases[0] | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const showNotification = () => {
      const randomPurchase = recentPurchases[Math.floor(Math.random() * recentPurchases.length)];
      setCurrentPurchase(randomPurchase);
      setIsVisible(true);
      
      setTimeout(() => {
        setIsVisible(false);
      }, 5000);
    };

    const initialDelay = setTimeout(showNotification, 8000);
    const interval = setInterval(showNotification, 25000);

    return () => {
      clearTimeout(initialDelay);
      clearInterval(interval);
    };
  }, []);

  if (!currentPurchase || !isVisible) return null;

  return (
    <div
      className="fixed bottom-24 left-6 z-40 max-w-xs animate-in slide-in-from-left duration-300"
      data-testid="social-proof-popup"
    >
      <div className="bg-card border rounded-md shadow-lg p-4 flex items-start gap-3">
        <div className="shrink-0 rounded-full bg-primary/10 p-2">
          <ShoppingBag className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            {currentPurchase.name} from {currentPurchase.location}
          </p>
          <p className="text-xs text-muted-foreground">
            just purchased {currentPurchase.product}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            a few moments ago
          </p>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="shrink-0 text-muted-foreground hover:text-foreground"
          data-testid="button-close-social-proof"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
