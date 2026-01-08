import { Package, CreditCard, Truck, HeadphonesIcon } from "lucide-react";

const features = [
  {
    icon: Package,
    title: "Direct Import Quality",
    description: "Authentic human hair imported directly from top suppliers. No middlemen, no compromises.",
  },
  {
    icon: CreditCard,
    title: "Flexible Payment",
    description: "Split your payment in two easy installments. Get your hair today, pay the rest later.",
  },
  {
    icon: Truck,
    title: "Fast Lagos Delivery",
    description: "Same-day delivery in Lagos. Nationwide delivery within 2-5 business days.",
  },
  {
    icon: HeadphonesIcon,
    title: "Expert Support",
    description: "Our hair experts are available on WhatsApp to help you find your perfect match.",
  },
];

export function WhyChooseUs() {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="font-serif text-3xl md:text-4xl font-bold mb-4">
            Why Choose GlowHair?
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Join thousands of satisfied customers who trust us for their hair needs
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="text-center p-6 rounded-md bg-card border"
              data-testid={`feature-${index}`}
            >
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-4">
                <feature.icon className="h-7 w-7 text-primary" />
              </div>
              <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
              <p className="text-muted-foreground text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
