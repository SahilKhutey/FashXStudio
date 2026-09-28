/**
 * FashXStudio — Navigation & Route Resolution Engine
 * Phase 01: Visual Product Architecture
 */

import { BreadcrumbItem, NavigationTabItem } from "./types";
import { SCREEN_INVENTORY } from "./inventory";

export const MAIN_NAVIGATION_TABS: NavigationTabItem[] = [
  {
    id: "tab-discover",
    label: "Discover",
    route: "/(tabs)/discover",
    iconName: "compass-outline",
    activeIconName: "compass",
  },
  {
    id: "tab-search",
    label: "Explore",
    route: "/(tabs)/search",
    iconName: "search-outline",
    activeIconName: "search",
  },
  {
    id: "tab-tryon",
    label: "Fitting Room",
    route: "/(tabs)/tryon",
    iconName: "sparkles-outline",
    activeIconName: "sparkles",
  },
  {
    id: "tab-closet",
    label: "Wardrobe",
    route: "/(tabs)/closet",
    iconName: "shirt-outline",
    activeIconName: "shirt",
  },
  {
    id: "tab-profile",
    label: "Profile",
    route: "/(tabs)/profile",
    iconName: "person-outline",
    activeIconName: "person",
  },
];

export function resolveBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) {
    return [{ label: "Home", route: "/(tabs)/discover", isCurrent: true }];
  }

  const breadcrumbs: BreadcrumbItem[] = [
    { label: "Home", route: "/(tabs)/discover", isCurrent: false },
  ];

  let currentPath = "";
  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    if (segment.startsWith("(") && segment.endsWith(")")) {
      continue;
    }
    currentPath += `/${segment}`;
    const matchedScreen = SCREEN_INVENTORY.find((s) => s.route === currentPath);
    const label = matchedScreen ? matchedScreen.title : segment.charAt(0).toUpperCase() + segment.slice(1);
    breadcrumbs.push({
      label,
      route: currentPath,
      isCurrent: i === segments.length - 1,
    });
  }

  return breadcrumbs;
}

export function isTabRoute(route: string): boolean {
  return MAIN_NAVIGATION_TABS.some((tab) => tab.route === route);
}
