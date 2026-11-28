import { useWindowDimensions } from "react-native";
import {
  getProductGridColumns,
  getScreenGutter,
  getScreenSize,
  type ScreenSize,
} from "../design-system/tokens/responsive";

export function getLayoutMetrics(width: number, height: number, fontScale: number) {
  const layout: ScreenSize = getScreenSize(width);
  const columns = getProductGridColumns(width);
  const horizontalPadding = getScreenGutter(width);

  return {
    width,
    height,
    fontScale,
    layout,
    columns,
    isCompact: layout === "compact",
    isTablet: layout === "tablet" || layout === "desktop",
    contentMaxWidth: 1120,
    horizontalPadding,
  };
}

export function useResponsiveLayout() {
  const { width, height, fontScale } = useWindowDimensions();
  return getLayoutMetrics(width, height, fontScale);
}
