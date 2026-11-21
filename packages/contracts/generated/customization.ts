/**
 * Canonical Customization Document Types
 * Generated from JSON Schema Draft 2020-12
 */

export interface DesignTokens {
  color: {
    brand: {
      primary: string;
      secondary?: string;
      accent?: string;
    };
    surface: {
      default: string;
      subtle?: string;
      raised?: string;
      overlay?: string;
    };
    text: {
      primary: string;
      secondary?: string;
      inverse?: string;
      muted?: string;
    };
    border: {
      default: string;
      subtle?: string;
      strong?: string;
    };
    status?: {
      success?: string;
      warning?: string;
      error?: string;
      info?: string;
    };
  };
  typography: {
    fontFamily: {
      body: string;
      heading: string;
      monospace?: string;
    };
    fontSize: {
      small: string;
      body: string;
      medium?: string;
      heading: string;
      display?: string;
    };
    fontWeight: {
      normal: 300 | 400;
      medium: 500 | 600;
      bold: 700 | 800 | 900;
    };
    lineHeight?: {
      tight?: string;
      normal?: string;
      relaxed?: string;
    };
    letterSpacing?: {
      normal?: string;
      wide?: string;
    };
  };
  spacing: {
    none?: string;
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl'?: string;
    '3xl'?: string;
  };
  radius: {
    none?: string;
    small: string;
    medium: string;
    large: string;
    full?: string;
  };
  shadow: {
    none?: string;
    small?: string;
    medium?: string;
    large?: string;
    card: string;
  };
  border?: {
    width?: {
      thin?: string;
      normal?: string;
      thick?: string;
    };
    style?: {
      solid?: 'solid';
      dashed?: 'dashed';
      dotted?: 'dotted';
    };
  };
  sizing?: {
    containerMaxWidth?: string;
    cardMinWidth?: string;
    imageAspectRatio?: '1/1' | '4/3' | '16/9' | '3/2';
  };
  motion?: {
    durationFast?: string;
    durationNormal?: string;
    durationSlow?: string;
    easingStandard?: string;
    reduceMotion?: boolean;
  };
  breakpoints?: {
    mobileSmall?: '320px';
    mobile?: '375px';
    tablet?: '768px';
    desktop?: '1024px';
    desktopLarge?: '1440px';
  };
  zIndex?: {
    dropdown?: number;
    modal?: number;
    tooltip?: number;
    overlay?: number;
  };
  accessibility?: {
    focusRingColor?: string;
    focusRingWidth?: string;
    minTouchTarget?: string;
  };
}

export interface DeepPartialTokens {
  color?: Partial<DesignTokens['color']>;
  typography?: Partial<DesignTokens['typography']>;
  spacing?: Partial<DesignTokens['spacing']>;
  radius?: Partial<DesignTokens['radius']>;
  shadow?: Partial<DesignTokens['shadow']>;
  border?: Partial<DesignTokens['border']>;
  sizing?: Partial<DesignTokens['sizing']>;
  motion?: Partial<DesignTokens['motion']>;
  breakpoints?: Partial<DesignTokens['breakpoints']>;
  zIndex?: Partial<DesignTokens['zIndex']>;
  accessibility?: Partial<DesignTokens['accessibility']>;
}

export type SlotName =
  | 'menu.root'
  | 'header'
  | 'navigation'
  | 'content'
  | 'category.header'
  | 'category.items'
  | 'footer';

export interface ComponentInstance {
  id: string;
  component_id: string;
  slot: SlotName;
  order: number;
  visible: boolean;
  props: Record<string, any>;
}

export interface LayoutSettings {
  columns?: number;
  density?: 'compact' | 'comfortable' | 'spacious';
  image_position?: 'top' | 'left' | 'right' | 'none';
  category_navigation_style?: 'pills' | 'tabs' | 'sticky-bar' | 'sidebar';
}

export interface ResponsiveProfileOverrides {
  columns?: number;
  density?: 'compact' | 'comfortable' | 'spacious';
}

export interface LayoutConfiguration {
  id: string;
  version: string;
  settings: LayoutSettings;
  responsive?: {
    mobileSmall?: ResponsiveProfileOverrides;
    mobile?: ResponsiveProfileOverrides;
    tablet?: ResponsiveProfileOverrides;
    desktop?: ResponsiveProfileOverrides;
    desktopLarge?: ResponsiveProfileOverrides;
  };
}

export interface ThemeConfiguration {
  id: string;
  version: string;
  overrides: DeepPartialTokens;
}

export interface MenuCustomization {
  configuration_version: string;
  schema_version: string;
  theme: ThemeConfiguration;
  layout: LayoutConfiguration;
  components: ComponentInstance[];
  metadata?: Record<string, any>;
}

export interface ResolvedCustomization {
  menu_id: string;
  revision: number;
  configuration_version: string;
  theme_id: string;
  theme_version: string;
  layout_id: string;
  layout_version: string;
  tokens: DesignTokens;
  css_variables: Record<string, string>;
  layout_settings: LayoutSettings;
  components_by_slot: Record<SlotName, ComponentInstance[]>;
  resolved_at: string;
}
