import { SiWhatsapp } from "react-icons/si";

export function WhatsAppFAB() {
  const whatsappNumber = "2348012345678";
  const message = encodeURIComponent(
    "Hi! I'm interested in your hair products. Can you help me?"
  );
  const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${message}`;

  return (
    <a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 right-6 z-50 bg-[#25D366] text-white p-4 rounded-full shadow-lg transition-transform hover:scale-110 active:scale-95"
      data-testid="button-whatsapp-fab"
      aria-label="Chat on WhatsApp"
    >
      <SiWhatsapp className="h-6 w-6" />
    </a>
  );
}
