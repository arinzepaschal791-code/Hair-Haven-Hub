import { Link } from "wouter";
import { MapPin, Phone, Mail, Clock, Instagram, Facebook } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

export function Footer() {
  return (
    <footer className="bg-card border-t">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div>
            <h3 className="font-serif text-2xl font-bold mb-4">
              Glow<span className="text-primary">Hair</span>
            </h3>
            <p className="text-muted-foreground text-sm mb-4">
              Premium imported bone straight hair and luxury wigs for the modern Nigerian woman. Quality you can trust.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://instagram.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                data-testid="link-instagram"
              >
                <Instagram className="h-5 w-5" />
              </a>
              <a
                href="https://facebook.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
                data-testid="link-facebook"
              >
                <Facebook className="h-5 w-5" />
              </a>
              <a
                href="https://wa.me/2348012345678"
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
                <span className="text-muted-foreground text-sm">
                  Track Your Order
                </span>
              </li>
              <li>
                <span className="text-muted-foreground text-sm">
                  Returns & Refunds
                </span>
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
                  Lekki Phase 1, Lagos, Nigeria
                </span>
              </li>
              <li className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-primary shrink-0" />
                <span className="text-muted-foreground text-sm">
                  +234 801 234 5678
                </span>
              </li>
              <li className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-primary shrink-0" />
                <span className="text-muted-foreground text-sm">
                  hello@glowhair.ng
                </span>
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
            2024 GlowHair Nigeria. All rights reserved.
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
