/**
 * FashXStudio — Fashion Content System Types (Phase 06)
 *
 * TypeScript contracts mirroring schemas/visual/fashion.py.
 * Covers 10 content objects, VisualContentModel, feed, save toggle, and templates.
 */

export type FashionContentType =
  | 'product'
  | 'look'
  | 'outfit'
  | 'collection'
  | 'style'
  | 'trend'
  | 'brand'
  | 'story'
  | 'article'
  | 'editorial'
  | 'recommendation';

export type ContentState =
  | 'loading'
  | 'loaded'
  | 'empty'
  | 'unavailable'
  | 'error'
  | 'partial';

export type ModerationState =
  | 'visible'
  | 'restricted'
  | 'unavailable'
  | 'removed'
  | 'pending';

export type TrendMomentum =
  | 'emerging'
  | 'peaking'
  | 'stable'
  | 'declining';

export type SaveState = 'unsaved' | 'saving' | 'saved' | 'error';

export type ContentSourceType =
  | 'official_merchant'
  | 'editorial'
  | 'community'
  | 'system_recommendation'
  | 'ai_generated';

export interface ProductItem {
  id: string;
  brand: string;
  title: string;
  primaryImageUri: string;
  alternateImageUris?: string[];
  price: {
    amount: number;
    originalAmount?: number;
    currencySymbol?: string;
    discountPercentage?: number;
  };
  rating?: {
    value: number;
    ratingCount?: number;
  };
  category: string;
  isSaved?: boolean;
  isInStock?: boolean;
  badge?: string;
  attributes?: Record<string, string>;
  state?: ContentState;
  moderationState?: ModerationState;
}

export interface LookItem {
  id: string;
  title: string;
  styleName: string;
  heroImageUri: string;
  itemsCount: number;
  associatedProductIds?: string[];
  tags?: string[];
  isSaved?: boolean;
  curatorName?: string;
  state?: ContentState;
}

export interface OutfitPieceMapping {
  slot: string;
  productId: string;
  productTitle: string;
  imageUri: string;
  price: { amount: number; currencySymbol?: string };
}

export interface OutfitItem {
  id: string;
  title: string;
  imageUri: string;
  pieces: OutfitPieceMapping[];
  isSaved?: boolean;
  totalPrice?: { amount: number; currencySymbol?: string };
  state?: ContentState;
}

export interface CollectionItem {
  id: string;
  title: string;
  description: string;
  heroImageUri: string;
  itemCount: number;
  seasonTag?: string;
  featuredProductIds?: string[];
  isSaved?: boolean;
  state?: ContentState;
}

export interface StyleCategory {
  id: string;
  name: string;
  description: string;
  imageUri: string;
  lookCount: number;
  associatedTags?: string[];
}

export interface TrendSignalPoint {
  timestamp: string;
  signalLabel: string;
  intensity: number;
}

export interface TrendItem {
  id: string;
  title: string;
  category: string;
  imageUri: string;
  momentum: TrendMomentum;
  regions: string[];
  timeline: TrendSignalPoint[];
  associatedProductIds?: string[];
  state?: ContentState;
}

export interface BrandItem {
  id: string;
  name: string;
  logoUri: string;
  coverImageUri?: string;
  category: string;
  description?: string;
  productCount: number;
  isVerified?: boolean;
}

export interface FashionStory {
  id: string;
  title: string;
  subtitle?: string;
  heroImageUri: string;
  author: string;
  publishedDate: string;
  contentMarkdown: string;
  category: string;
  relatedProductIds?: string[];
  relatedLookIds?: string[];
  state?: ContentState;
}

export interface RecommendationItem {
  id: string;
  targetContentType: FashionContentType;
  product: ProductItem;
  recommendationLabel: string;
  explanationReason: string;
  confidenceScore: number;
  sourceType: ContentSourceType;
}

export interface VisualContent {
  id: string;
  contentType: FashionContentType;
  title: string;
  subtitle?: string;
  mediaUri: string;
  categoryLabel: string;
  price?: { amount: number; originalAmount?: number; currencySymbol?: string };
  rating?: { value: number; ratingCount?: number };
  labels?: string[];
  isSaved?: boolean;
  state?: ContentState;
  source?: ContentSourceType;
  relationships?: Record<string, string[]>;
}

export interface FashionFeed {
  feedId: string;
  title: string;
  items: VisualContent[];
  hasPartialContent: boolean;
  totalItems: number;
}

export interface SaveToggleResult {
  contentId: string;
  contentType: FashionContentType;
  isSaved: boolean;
  state: SaveState;
  message: string;
}
