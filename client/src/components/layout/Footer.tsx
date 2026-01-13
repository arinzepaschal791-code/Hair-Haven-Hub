import { Link } from "wouter";
import { MapPin, Phone, Clock, Instagram, Facebook } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import logoImage from "@assets/nora_logo_1768342898279.jpg";

export function Footer() {
  return (
    <footer className="bg-card border-t">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div>
            <div className="flex items-start mb-3">
              <img 
                src={logoImage} 
                alt="NORA HAIR LINE" 
                className="h-20 w-auto object-contain"
              />
            </div>
            <p className="text-muted-foreground text-sm mb-4">
              Premium Closure, Frontals, 360 Illusion Frontal, Wigs & Bundles. Quality you can trust at affordable prices.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://instagram.com/norahairline"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                data-testid="link-instagram"
              >
                <Instagram className="h-5 w-5" />
              </a>
              <a
                href="https://facebook.com/norahairline"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                data-testid="link-facebook"
              >
                <Facebook className="h-5 w-5" />
              </a>
              <a
                href="https://wa.me/2348038707795"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                data-testid="link-whatsapp"
              >
                <SiWhatsapp className="h-5 w-5" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/shop">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-shop">
                    Shop All
                  </span>
                </Link>
              </li>
              <li>
                <Link href="/bone-straight">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-bone-straight">
                    Bone Straight
                  </span>
                </Link>
              </li>
              <li>
                <Link href="/wigs">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-wigs">
                    Wigs
                  </span>
                </Link>
              </li>
              <li>
                <Link href="/about">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-about">
                    About Us
                  </span>
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Customer Care</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/track-order">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-track-order">
                    Track Your Order
                  </span>
                </Link>
              </li>
              <li>
                <Link href="/wishlist">
                  <span className="text-muted-foreground hover:text-primary transition-colors text-sm cursor-pointer" data-testid="link-footer-wishlist">
                    My Wishlist
                  </span>
                </Link>
              </li>
              <li>
                <span className="text-muted-foreground text-sm">
                  Hair Care Guide
                </span>
              </li>
              <li>
                <span className="text-muted-foreground text-sm">
                  FAQs
                </span>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Contact Us</h4>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <span className="text-muted-foreground text-sm">
                  No 5 Veet Gold Plaza, directly opposite Abia Gate @ Tradefair Shopping Center, Badagry Express Way, Lagos State
                </span>
              </li>
              <li className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-primary shrink-0" />
                <a href="tel:+2348038707795" className="text-muted-foreground hover:text-primary text-sm">
                  0803 870 7795
                </a>
              </li>
              <li className="flex items-center gap-3">
                <SiWhatsapp className="h-5 w-5 text-[#25D366] shrink-0" />
                <a href="https://wa.me/2348038707795" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary text-sm">
                  WhatsApp: 0803 870 7795
                </a>
              </li>
              <li className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-primary shrink-0" />
                <span className="text-muted-foreground text-sm">
                  Mon - Sat: 9AM - 7PM
                </span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-muted-foreground text-sm text-center md:text-left">
            2024 NORA HAIR LINE. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-muted-foreground text-sm">
              Privacy Policy
            </span>
            <span className="text-muted-foreground text-sm">
              Terms of Service
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
