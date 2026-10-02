/**
 * FashXStudio useResponsive Hook — Version 1.
 *
 * Implements the semantic responsive query API established in Section 14.88.
 * Provides accessible, declarative viewport state without scattered breakpoint checks.
 */

import { useState, useEffect } from 'react';
import { useWindowDimensions, Platform, AccessibilityInfo } from 'react-native';
import {
  ResponsiveBreakpoint,
  LayoutMode,
  DeviceOrientation,
  ResponsiveContainerContract,
} from '../types';

export interface UseResponsiveResult {
  width: number;
  height: number;
  breakpoint: ResponsiveBreakpoint;
  layoutMode: LayoutMode;
  orientation: DeviceOrientation;
  isCompact: boolean;
  isAdaptive: boolean;
  isExpanded: boolean;
  isTouch: boolean;
  isLandscape: boolean;
  isPortrait: boolean;
  isReducedMotion: boolean;
  containerMaxWidth: number;
  horizontalPadding: number;
  gutter: number;
  defaultColumns: number;
}

export function useResponsive(): UseResponsiveResult {
  const { width, height } = useWindowDimensions();
  const [isReducedMotion, setIsReducedMotion] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (isMounted) {
        setIsReducedMotion(enabled);
      }
    });

    const subscription = AccessibilityInfo.addEventListener(
      'reduceMotionChanged',
      (enabled) => {
        setIsReducedMotion(enabled);
      }
    );

    return () => {
      isMounted = false;
      subscription?.remove();
    };
  }, []);

  // Breakpoint resolution (Section 14.3)
  let breakpoint: ResponsiveBreakpoint = 'xs';
  let containerMaxWidth = 480;
  let horizontalPadding = 16;
  let gutter = 12;
  let defaultColumns = 4;

  if (width < 480) {
    breakpoint = 'xs';
    containerMaxWidth = 480;
    horizontalPadding = 16;
    gutter = 12;
    defaultColumns = 4;
  } else if (width < 768) {
    breakpoint = 'sm';
    containerMaxWidth = 720;
    horizontalPadding = 16;
    gutter = 16;
    defaultColumns = 4;
  } else if (width < 1024) {
    breakpoint = 'md';
    containerMaxWidth = 960;
    horizontalPadding = 24;
    gutter = 20;
    defaultColumns = 8;
  } else if (width < 1280) {
    breakpoint = 'lg';
    containerMaxWidth = 1200;
    horizontalPadding = 24;
    gutter = 24;
    defaultColumns = 12;
  } else if (width < 1536) {
    breakpoint = 'xl';
    containerMaxWidth = 1440;
    horizontalPadding = 32;
    gutter = 24;
    defaultColumns = 12;
  } else {
    breakpoint = '2xl';
    containerMaxWidth = 1600;
    horizontalPadding = 32;
    gutter = 32;
    defaultColumns = 12;
  }

  // Layout mode resolution (Section 14.4)
  let layoutMode: LayoutMode = 'compact';
  if (width < 768) {
    layoutMode = 'compact';
  } else if (width < 1024) {
    layoutMode = 'adaptive';
  } else {
    layoutMode = 'expanded';
  }

  const orientation: DeviceOrientation = width >= height ? 'landscape' : 'portrait';
  const isTouch = Platform.OS === 'ios' || Platform.OS === 'android';

  return {
    width,
    height,
    breakpoint,
    layoutMode,
    orientation,
    isCompact: layoutMode === 'compact',
    isAdaptive: layoutMode === 'adaptive',
    isExpanded: layoutMode === 'expanded',
    isTouch,
    isLandscape: orientation === 'landscape',
    isPortrait: orientation === 'portrait',
    isReducedMotion,
    containerMaxWidth,
    horizontalPadding,
    gutter,
    defaultColumns,
  };
}
