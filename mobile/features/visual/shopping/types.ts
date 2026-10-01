/**
 * FashXStudio Mobile Shopping UI System Types — Phase 07.
 *
 * Mirrors backend Pydantic contracts from schemas.visual.shopping (Sections 7.1-7.83).
 */

import { PriceSpec, RatingSpec } from "../components/types";

export type ProductAvailabilityState =
  | "in_stock"
  | "low_stock"
  | "out_of_stock"
  | "unavailable"
  | "preorder";

export type VariantType = "size" | "color" | "material" | "style";

export type VariantState = "available" | "selected" | "unavailable" | "disabled" | "loading";

export type SortOption = "relevance" | "newest" | "price_asc" | "price_desc" | "popularity";

export type FilterType = "checkbox" | "radio" | "range" | "swatch";

export type ShoppingState =
  | "loading"
  | "ready"
  | "empty"
  | "partial"
  | "validation_error"
  | "service_error"
  | "unavailable"
  | "success";

export type OrderStatus =
  | "placed"
  | "processing"
  | "shipped"
  | "out_for_delivery"
  | "delivered"
  | "cancelled"
  | "returned"
  | "refunded";

export type CheckoutStep =
  | "contact"
  | "address"
  | "delivery"
  | "payment"
  | "review"
  | "confirmation";

export type ShoppingScreenId =
  | "SH01"
  | "SH02"
  | "SH03"
  | "SH04"
  | "SH05"
  | "SH06"
  | "SH07"
  | "SH08"
  | "SH09"
  | "SH10"
  | "SH11"
  | "SH12";

// --- Filters & Sorting ---

export interface FilterOption {
  id: string;
  label: string;
  value: string;
  count?: number;
  isSelected?: boolean;
}

export interface FilterGroup {
  id: string;
  name: string;
  filterType: FilterType;
  options: FilterOption[];
}

export interface ActiveFilter {
  groupId: string;
  optionId: string;
  label: string;
}

export interface FilterState {
  availableGroups: FilterGroup[];
  activeFilters: ActiveFilter[];
  totalMatches: number;
}

// --- Product & Variants ---

export interface ProductVariantOption {
  id: string;
  variantType: VariantType;
  value: string;
  label: string;
  state: VariantState;
  swatchHex?: string;
  priceDelta?: number;
}

export interface ProductVariantGroup {
  id: string;
  variantType: VariantType;
  title: string;
  options: ProductVariantOption[];
}

export interface DeliveryInfo {
  estimatedDeliveryDays: string;
  shippingFee: number;
  isFreeDelivery: boolean;
  postalCode?: string;
}

export interface SpecificationAttribute {
  name: string;
  value: string;
  category?: string;
}

export interface CompleteTheLookSlot {
  slotName: string;
  productId: string;
  productTitle: string;
  price: PriceSpec;
  mediaUri: string;
}

export interface ShoppingProductDetail {
  id: string;
  brand: string;
  title: string;
  primaryMediaUri: string;
  mediaGallery: string[];
  price: PriceSpec;
  availability: ProductAvailabilityState;
  stockCount?: number;
  description: string;
  rating?: RatingSpec;
  variantGroups: ProductVariantGroup[];
  deliveryInfo?: DeliveryInfo;
  specifications: SpecificationAttribute[];
  completeTheLook: CompleteTheLookSlot[];
  relatedProductIds: string[];
  isInWishlist: boolean;
}

// --- Cart & Wishlist ---

export interface CartItem {
  itemId: string;
  productId: string;
  title: string;
  brand: string;
  mediaUri: string;
  selectedVariants: Record<string, string>;
  quantity: number;
  unitPrice: PriceSpec;
  totalPrice: PriceSpec;
  availability: ProductAvailabilityState;
}

export interface CartSummary {
  subtotal: number;
  discount: number;
  deliveryFee: number;
  total: number;
  currencySymbol: string;
  itemCount: number;
}

export interface Cart {
  cartId: string;
  items: CartItem[];
  summary: CartSummary;
  state: ShoppingState;
  validationErrors: string[];
}

export interface CartValidationResult {
  isValid: boolean;
  hasPriceChange: boolean;
  hasOutOfStock: boolean;
  messages: string[];
}

export interface WishlistItem {
  itemId: string;
  productId: string;
  title: string;
  brand: string;
  mediaUri: string;
  price: PriceSpec;
  availability: ProductAvailabilityState;
  addedTimestamp: string;
}

export interface Wishlist {
  wishlistId: string;
  userId: string;
  items: WishlistItem[];
  totalCount: number;
}

// --- Checkout & Orders ---

export interface DeliveryAddress {
  id: string;
  fullName: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  phone: string;
  isDefault?: boolean;
}

export interface DeliveryMethod {
  id: string;
  name: string;
  description: string;
  fee: number;
  estimatedTime: string;
}

export interface PaymentMethod {
  id: string;
  methodType: string;
  title: string;
  last4?: string;
  isSelected?: boolean;
}

export interface CheckoutState {
  checkoutId: string;
  currentStep: CheckoutStep;
  cart: Cart;
  deliveryAddress?: DeliveryAddress;
  deliveryMethod?: DeliveryMethod;
  paymentMethod?: PaymentMethod;
  isReadyToPlace: boolean;
}

export interface OrderItem {
  productId: string;
  title: string;
  brand: string;
  mediaUri: string;
  selectedVariants: Record<string, string>;
  quantity: number;
  unitPrice: PriceSpec;
  totalPrice: PriceSpec;
}

export interface Order {
  orderId: string;
  orderNumber: string;
  placedAt: string;
  status: OrderStatus;
  items: OrderItem[];
  deliveryAddress: DeliveryAddress;
  deliveryMethod: DeliveryMethod;
  paymentSummary: string;
  priceSummary: CartSummary;
}

// --- Templates ---

export interface ShoppingHomeTemplateSpec {
  screenId: ShoppingScreenId;
  searchPlaceholder: string;
  featuredCollectionIds: string[];
  categories: Array<{ id: string; name: string; image_uri: string }>;
  trendingProductIds: string[];
  recommendedProductIds: string[];
}

export interface CategoryTemplateSpec {
  screenId: ShoppingScreenId;
  categoryId: string;
  categoryName: string;
  parentCategoryName?: string;
  subcategories: Array<{ id: string; name: string }>;
  featuredProductIds: string[];
}

export interface SearchResultsTemplateSpec {
  query: string;
  totalResults: number;
  suggestions: string[];
  filterState: FilterState;
  productIds: string[];
}

export interface ProductDetailTemplateSpec {
  product: ShoppingProductDetail;
  breadcrumbTrail: string[];
  stickyActionEnabled: boolean;
}

export interface WishlistTemplateSpec {
  screenId: ShoppingScreenId;
  wishlist: Wishlist;
  sortOptions: string[];
}

export interface CartTemplateSpec {
  screenId: ShoppingScreenId;
  cart: Cart;
  suggestedCrossSellIds: string[];
}

export interface CheckoutTemplateSpec {
  screenId: ShoppingScreenId;
  checkoutState: CheckoutState;
  availableAddresses: DeliveryAddress[];
  availableDeliveryMethods: DeliveryMethod[];
  availablePaymentMethods: PaymentMethod[];
}

export interface ConfirmationTemplateSpec {
  screenId: ShoppingScreenId;
  orderNumber: string;
  orderId: string;
  placedAt: string;
  estimatedDelivery: string;
  itemsCount: number;
  totalAmount: number;
  currencySymbol: string;
}

export interface OrdersTemplateSpec {
  screenId: ShoppingScreenId;
  orders: Order[];
  totalOrders: number;
}

export interface OrderDetailTemplateSpec {
  screenId: ShoppingScreenId;
  order: Order;
  trackingSteps: Array<{ step: string; status: string; time: string }>;
}
