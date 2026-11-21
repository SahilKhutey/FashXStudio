import type { DesignTokens } from './customization';

export interface ThemeDefinition {
  schema_version: string;
  id: string;
  name: string;
  version: string;
  status: 'active' | 'deprecated' | 'retired';
  description?: string;
  preview_image_url?: string;
  tokens: DesignTokens;
  supported_layouts: string[];
  supported_components: string[];
  accessibility?: {
    contrast_ratio_normal?: number;
    contrast_ratio_large?: number;
    wcag_level?: 'AA' | 'AAA';
  };
  metadata?: Record<string, any>;
}
