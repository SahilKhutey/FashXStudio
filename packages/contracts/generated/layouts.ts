import type { LayoutSettings, ResponsiveProfileOverrides, SlotName } from './customization';

export interface LayoutDefinition {
  schema_version: string;
  id: string;
  name: string;
  version: string;
  status: 'active' | 'deprecated' | 'retired';
  description?: string;
  supported_slots: SlotName[];
  allowed_components_by_slot: Partial<Record<SlotName, string[]>>;
  default_settings: LayoutSettings;
  responsive_profiles: {
    mobileSmall?: ResponsiveProfileOverrides;
    mobile: ResponsiveProfileOverrides;
    tablet?: ResponsiveProfileOverrides;
    desktop: ResponsiveProfileOverrides;
    desktopLarge?: ResponsiveProfileOverrides;
  };
}
