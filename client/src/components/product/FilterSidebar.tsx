import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { X } from "lucide-react";

export interface FilterState {
  categories: string[];
  lengths: string[];
  priceRange: [number, number];
  inStockOnly: boolean;
}

interface FilterSidebarProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  onClose?: () => void;
  isMobile?: boolean;
}

const categories = [
  { value: "bone-straight", label: "Bone Straight" },
  { value: "wig", label: "Wigs" },
  { value: "hair-care", label: "Hair Care" },
];

const lengths = [
  { value: "10", label: "10 inches" },
  { value: "12", label: "12 inches" },
  { value: "14", label: "14 inches" },
  { value: "16", label: "16 inches" },
  { value: "18", label: "18 inches" },
  { value: "20", label: "20 inches" },
  { value: "22", label: "22 inches" },
  { value: "24", label: "24 inches" },
];

export function FilterSidebar({
  filters,
  onFilterChange,
  onClose,
  isMobile = false,
}: FilterSidebarProps) {
  const [localPriceRange, setLocalPriceRange] = useState<[number, number]>(
    filters.priceRange
  );

  const handleCategoryChange = (value: string, checked: boolean) => {
    const newCategories = checked
      ? [...filters.categories, value]
      : filters.categories.filter((c) => c !== value);
    onFilterChange({ ...filters, categories: newCategories });
  };

  const handleLengthChange = (value: string, checked: boolean) => {
    const newLengths = checked
      ? [...filters.lengths, value]
      : filters.lengths.filter((l) => l !== value);
    onFilterChange({ ...filters, lengths: newLengths });
  };

  const handlePriceChange = (value: number[]) => {
    setLocalPriceRange([value[0], value[1]]);
  };

  const handlePriceCommit = () => {
    onFilterChange({ ...filters, priceRange: localPriceRange });
  };

  const handleClearFilters = () => {
    const clearedFilters: FilterState = {
      categories: [],
      lengths: [],
      priceRange: [0, 500000],
      inStockOnly: false,
    };
    onFilterChange(clearedFilters);
    setLocalPriceRange([0, 500000]);
  };

  const hasActiveFilters =
    filters.categories.length > 0 ||
    filters.lengths.length > 0 ||
    filters.priceRange[0] > 0 ||
    filters.priceRange[1] < 500000 ||
    filters.inStockOnly;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Filters</h3>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilters}
              data-testid="button-clear-filters"
            >
              Clear All
            </Button>
          )}
          {isMobile && onClose && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              data-testid="button-close-filters"
            >
              <X className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>

      <Accordion type="multiple" defaultValue={["category", "length", "price"]} className="w-full">
        <AccordionItem value="category">
          <AccordionTrigger className="text-sm font-medium">
            Category
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3 pt-2">
              {categories.map((category) => (
                <div key={category.value} className="flex items-center gap-2">
                  <Checkbox
                    id={`category-${category.value}`}
                    checked={filters.categories.includes(category.value)}
                    onCheckedChange={(checked) =>
                      handleCategoryChange(category.value, checked === true)
                    }
                    data-testid={`checkbox-category-${category.value}`}
                  />
                  <Label
                    htmlFor={`category-${category.value}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {category.label}
                  </Label>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="length">
          <AccordionTrigger className="text-sm font-medium">
            Length
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3 pt-2">
              {lengths.map((length) => (
                <div key={length.value} className="flex items-center gap-2">
                  <Checkbox
                    id={`length-${length.value}`}
                    checked={filters.lengths.includes(length.value)}
                    onCheckedChange={(checked) =>
                      handleLengthChange(length.value, checked === true)
                    }
                    data-testid={`checkbox-length-${length.value}`}
                  />
                  <Label
                    htmlFor={`length-${length.value}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {length.label}
                  </Label>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="price">
          <AccordionTrigger className="text-sm font-medium">
            Price Range
          </AccordionTrigger>
          <AccordionContent>
            <div className="pt-4 px-1">
              <Slider
                min={0}
                max={500000}
                step={5000}
                value={localPriceRange}
                onValueChange={handlePriceChange}
                onValueCommit={handlePriceCommit}
                data-testid="slider-price"
              />
              <div className="flex items-center justify-between mt-3 text-sm text-muted-foreground">
                <span>N{localPriceRange[0].toLocaleString()}</span>
                <span>N{localPriceRange[1].toLocaleString()}</span>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="availability">
          <AccordionTrigger className="text-sm font-medium">
            Availability
          </AccordionTrigger>
          <AccordionContent>
            <div className="flex items-center gap-2 pt-2">
              <Checkbox
                id="in-stock"
                checked={filters.inStockOnly}
                onCheckedChange={(checked) =>
                  onFilterChange({ ...filters, inStockOnly: checked === true })
                }
                data-testid="checkbox-in-stock"
              />
              <Label
                htmlFor="in-stock"
                className="text-sm font-normal cursor-pointer"
              >
                In Stock Only
              </Label>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
