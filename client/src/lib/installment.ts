export const INSTALLMENT_ELIGIBLE_CATEGORIES = ["bone-straight", "wig"];

export function isInstallmentEligible(category: string): boolean {
  return INSTALLMENT_ELIGIBLE_CATEGORIES.includes(category);
}

export function hasInstallmentEligibleItems(items: Array<{ category?: string }>): boolean {
  return items.some(item => item.category && isInstallmentEligible(item.category));
}

export function allItemsInstallmentEligible(items: Array<{ category?: string }>): boolean {
  return items.every(item => item.category && isInstallmentEligible(item.category));
}
