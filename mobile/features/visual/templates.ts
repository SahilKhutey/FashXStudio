/**
 * FashXStudio — Reusable Page Templates Architecture
 * Visual Design — 1: Section 1.24 Template Architecture
 * 11 Reusable Page Templates unifying the 123 screens.
 */

import { PageTemplateType } from "./types";

export interface TemplateDefinition {
  type: PageTemplateType;
  title: string;
  description: string;
  defaultLayout: "single_column" | "split_pane" | "grid" | "canvas" | "full_bleed";
  primaryComponents: string[];
  supportedScreensCount: number;
}

export const PAGE_TEMPLATES: Record<PageTemplateType, TemplateDefinition> = {
  listing: {
    type: "listing",
    title: "Listing Template",
    description: "Multi-item grid / collection feed with filter chips, sorting dropdowns, and infinite scroll.",
    defaultLayout: "grid",
    primaryComponents: ["ProductGrid", "FilterBar", "SortControl", "CardCollection"],
    supportedScreensCount: 32,
  },
  detail: {
    type: "detail",
    title: "Detail Template",
    description: "High-information single entity display featuring image hero gallery, specifications, and primary actions.",
    defaultLayout: "split_pane",
    primaryComponents: ["HeroGallery", "SpecSheet", "ActionRail", "RecommendationCarousel"],
    supportedScreensCount: 14,
  },
  discovery: {
    type: "discovery",
    title: "Discovery Template",
    description: "Serendipitous exploration layout mixing horizontal rails, thematic hero cards, and stylist chips.",
    defaultLayout: "grid",
    primaryComponents: ["CuratedRail", "ThemeBanner", "StylistChip", "MasonryFeed"],
    supportedScreensCount: 15,
  },
  editorial: {
    type: "editorial",
    title: "Editorial Template",
    description: "Magazine-style narrative layout with high-impact typography, full-bleed imagery, and shoppable links.",
    defaultLayout: "full_bleed",
    primaryComponents: ["ArticleHeader", "StoryViewer", "LookbookCanvas", "ShoppableHotspots"],
    supportedScreensCount: 8,
  },
  builder: {
    type: "builder",
    title: "Builder Template",
    description: "Creative interactive workspace for freeform outfit composition, layer sorting, and mix-matching.",
    defaultLayout: "canvas",
    primaryComponents: ["StylingCanvas", "LayerStackManager", "CompatibilityMeter", "SlotCarousel"],
    supportedScreensCount: 3,
  },
  map: {
    type: "map",
    title: "Map Template",
    description: "Interactive geographic exploration canvas with cluster pins, regional trend drawers, and spatial filtering.",
    defaultLayout: "full_bleed",
    primaryComponents: ["GeoCanvas", "ClusterMarker", "RegionalDrawer", "LocalMerchantCard"],
    supportedScreensCount: 7,
  },
  dashboard: {
    type: "dashboard",
    title: "Dashboard Template",
    description: "Multi-widget summary hub presenting key metrics, status indicators, and shortcut tiles.",
    defaultLayout: "single_column",
    primaryComponents: ["MetricCard", "QuickActionTile", "TimelineWidget", "StatusBanner"],
    supportedScreensCount: 18,
  },
  assistant: {
    type: "assistant",
    title: "Assistant Template",
    description: "Conversational intelligence interface with turn-based dialogue, rationale cards, and action pills.",
    defaultLayout: "single_column",
    primaryComponents: ["ChatTranscript", "PromptInput", "RationaleDrawer", "SuggestedActionPills"],
    supportedScreensCount: 5,
  },
  comparison: {
    type: "comparison",
    title: "Comparison Template",
    description: "Side-by-side columnar comparison of garment attributes, prices, merchant stocks, and fit biases.",
    defaultLayout: "split_pane",
    primaryComponents: ["ComparisonMatrix", "SpecRow", "DifferenceHighlight", "MultiMerchantCTA"],
    supportedScreensCount: 1,
  },
  checkout: {
    type: "checkout",
    title: "Checkout Template",
    description: "Structured step-by-step commerce flow with line items, price breakdowns, and handoff buttons.",
    defaultLayout: "single_column",
    primaryComponents: ["CartLineList", "OrderSummaryCard", "ShippingSelector", "CheckoutHandoffCTA"],
    supportedScreensCount: 4,
  },
  settings: {
    type: "settings",
    title: "Settings Template",
    description: "Form-based configuration screen with segmented controls, preference toggles, and disclosure rows.",
    defaultLayout: "single_column",
    primaryComponents: ["PreferenceGroup", "ToggleRow", "SliderControl", "SaveButton"],
    supportedScreensCount: 16,
  },
};
