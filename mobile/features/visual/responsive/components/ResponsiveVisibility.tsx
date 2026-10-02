/**
 * ResponsiveVisibility — Semantic conditional display wrapper (Section 14.90).
 *
 * Renders or unmounts children based on layout mode, avoiding arbitrary CSS display:none.
 */

import React, { ReactNode } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { LayoutMode } from '../types';

interface ResponsiveVisibilityProps {
  children: ReactNode;
  visibleIn?: LayoutMode[];
  hiddenIn?: LayoutMode[];
}

export const ResponsiveVisibility: React.FC<ResponsiveVisibilityProps> = ({
  children,
  visibleIn,
  hiddenIn,
}) => {
  const { layoutMode } = useResponsive();

  if (hiddenIn && hiddenIn.includes(layoutMode)) {
    return null;
  }

  if (visibleIn && !visibleIn.includes(layoutMode)) {
    return null;
  }

  return <>{children}</>;
};
