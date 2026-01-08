import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Star, Quote } from "lucide-react";
import customerImg1 from "@assets/stock_images/beautiful_african_wo_8e308ce0.jpg";
import customerImg2 from "@assets/stock_images/beautiful_african_wo_217fa6d2.jpg";
import customerImg3 from "@assets/stock_images/woman_long_straight__1bf9cbec.jpg";

const testimonials = [
  {
    id: 1,
    name: "Amara Okonkwo",
    location: "Lagos",
    content: "The bone straight hair I got is absolutely amazing! It's been 6 months and it still looks brand new. Best hair vendor in Nigeria!",
    rating: 5,
    image: customerImg1,
    productPurchased: "Bone Straight 22\"",
  },
  {
    id: 2,
    name: "Blessing Eze",
    location: "Abuja",
    content: "The installment payment option was a lifesaver. I got my dream wig without breaking the bank. Customer service is top-notch too!",
    rating: 5,
    image: customerImg2,
    productPurchased: "Luxury Frontal Wig",
  },
  {
    id: 3,
    name: "Chidinma Nwachukwu",
    location: "Port Harcourt",
    content: "Fast delivery and the hair quality exceeded my expectations. Will definitely be ordering again. Thank you NORAHAIRLINE!",
    rating: 5,
    image: customerImg3,
    productPurchased: "Bone Straight 18\"",
  },
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < rating ? "text-yellow-500 fill-yellow-500" : "text-muted"
          }`}
        />
      ))}
    </div>
  );
}

export function Testimonials() {
  return (
    <section className="py-16 md:py-24 bg-card">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="font-serif text-3xl md:text-4xl font-bold mb-4">
            What Our Customers Say
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Join over 5,000 satisfied customers who trust NORAHAIRLINE for their beauty needs
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial) => (
            <Card key={testimonial.id} className="bg-background" data-testid={`testimonial-${testimonial.id}`}>
              <CardContent className="p-6">
                <Quote className="h-8 w-8 text-primary/20 mb-4" />
                <p className="text-foreground mb-6 leading-relaxed">
                  "{testimonial.content}"
                </p>
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={testimonial.image} alt={testimonial.name} />
                    <AvatarFallback>{testimonial.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.location}</p>
                  </div>
                  <StarRating rating={testimonial.rating} />
                </div>
                <p className="text-xs text-muted-foreground mt-4 pt-4 border-t">
                  Purchased: {testimonial.productPurchased}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
