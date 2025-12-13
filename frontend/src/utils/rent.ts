import type { Listing } from '../types';
import { ListingWithScore } from '../components/ListingsPanel';

// Convert weekly rent to monthly (52 weeks / 12 months)
export const weeklyToMonthly = (weeklyPrice: number): number => Math.round(weeklyPrice * 52 / 12);

// Parse rent and normalize to monthly
export const normalizeRent = (listing: Listing): ListingWithScore => {
    const summary = (listing.summary || '').toLowerCase();
    const isWeekly = summary.includes('pw') || summary.includes('per week') || summary.includes('/week');
    const price = listing.price || 0;
    return {
        ...listing,
        price: isWeekly ? weeklyToMonthly(price) : price,
        priceLabel: isWeekly ? `£${price}pw (£${weeklyToMonthly(price)}/mo)` : `£${price}/month`
    };
};
