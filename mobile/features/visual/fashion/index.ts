/**
 * FashXStudio — Fashion Content System Public API (Phase 06)
 *
 * Barrel export for:
 * - Content Types
 * - Product, Look, Outfit, Collection, Trend, Brand, Story, Recommendation components
 * - Content Templates (Discovery, Listing)
 */

export * from './types';

// Components
export * from './product/ProductCard';
export * from './look/LookCard';
export * from './outfit/OutfitCard';
export * from './collection/CollectionCard';
export * from './trend/TrendCard';
export * from './trend/TrendTimeline';
export * from './brand/BrandCard';
export * from './editorial/StoryCard';
export * from './recommendation/RecommendationCard';

// Templates
export * from './templates/DiscoveryTemplate';
export * from './templates/ListingTemplate';
