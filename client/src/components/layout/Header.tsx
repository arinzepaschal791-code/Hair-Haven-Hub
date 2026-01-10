import { useState } from "react";
import { Link, useLocation } from "wouter";
import { ShoppingCart, Menu, X, Search, User, Moon, Sun, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useCart } from "@/lib/cart";
import { useWishlist } from "@/lib/wishlist";
import { useTheme } from "@/lib/theme";
import logoImage from "@assets/nora_logo_transparent.png";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/shop", label: "Shop" },
  { href: "/bone-straight", label: "Bone Straight" },
  { href: "/wigs", label: "Wigs" },
  { href: "/about", label: "About" },
];

export function Header() {
  const [location] = useLocation();
  const { totalItems } = useCart();
  const { totalItems: wishlistCount } = useWishlist();
  const { theme, toggleTheme } = useTheme();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between gap-4 h-16">
          <Link href="/">
            <div className="flex items-center gap-3 cursor-pointer" data-testid="link-logo">
              <img 
                src={logoImage} 
                alt="NORA HAIR LINE Logo" 
                className="h-12 w-auto object-contain"
              />
              <div className="hidden sm:flex flex-col leading-tight">
                <span className="font-serif text-lg font-bold tracking-wide text-foreground">
                  NORA HAIR LINE
                </span>
                <span className="text-[10px] text-primary italic">Luxury for less...</span>
              </div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link key={link.href} href={link.href}>
                <span
                  className={`text-sm font-medium transition-colors hover:text-primary cursor-pointer ${
                    location === link.href
                      ? "text-primary"
                      : "text-muted-foreground"
                  }`}
                  data-testid={`link-nav-${link.label.toLowerCase().replace(" ", "-")}`}
                >
                  {link.label}
                </span>
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {isSearchOpen ? (
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Search products..."
                  className="w-48 md:w-64"
                  data-testid="input-search"
                />
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setIsSearchOpen(false)}
                  data-testid="button-close-search"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            ) : (
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setIsSearchOpen(true)}
                data-testid="button-open-search"
              >
                <Search className="h-5 w-5" />
              </Button>
            )}

            <Button
              size="icon"
              variant="ghost"
              onClick={toggleTheme}
              data-testid="button-theme-toggle"
            >
              {theme === "light" ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </Button>

            <Link href="/wishlist">
              <Button size="icon" variant="ghost" className="relative" data-testid="button-wishlist">
                <Heart className="h-5 w-5" />
                {wishlistCount > 0 && (
                  <Badge
                    variant="secondary"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                  >
                    {wishlistCount}
                  </Badge>
                )}
              </Button>
            </Link>

            <Link href="/cart">
              <Button size="icon" variant="ghost" className="relative" data-testid="button-cart">
                <ShoppingCart className="h-5 w-5" />
                {totalItems > 0 && (
                  <Badge
                    variant="default"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                  >
                    {totalItems}
                  </Badge>
                )}
              </Button>
            </Link>

            <Link href="/admin" className="hidden md:block">
              <Button size="icon" variant="ghost" data-testid="button-admin">
                <User className="h-5 w-5" />
              </Button>
            </Link>

            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild className="md:hidden">
                <Button size="icon" variant="ghost" data-testid="button-mobile-menu">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72">
                <nav className="flex flex-col gap-4 mt-8">
                  {navLinks.map((link) => (
                    <Link key={link.href} href={link.href}>
                      <span
                        className={`text-lg font-medium transition-colors cursor-pointer block py-2 ${
                          location === link.href
                            ? "text-primary"
                            : "text-foreground"
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                        data-testid={`link-mobile-${link.label.toLowerCase().replace(" ", "-")}`}
                      >
                        {link.label}
                      </span>
                    </Link>
                  ))}
                  <Link href="/admin">
                    <span
                      className="text-lg font-medium text-foreground cursor-pointer block py-2"
                      onClick={() => setMobileMenuOpen(false)}
                      data-testid="link-mobile-admin"
                    >
                      Admin
                    </span>
                  </Link>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  );
}
