import type { SlotName } from './customization';

export interface ComponentDefinition {
  schema_version: string;
  id: string;
  name: string;
  version: string;
  status: 'active' | 'deprecated' | 'retired';
  category: 'header' | 'navigation' | 'layout' | 'item' | 'feedback' | 'footer';
  allowed_slots: SlotName[];
  property_schema: Record<string, any>;
  default_props: Record<string, any>;
  accessibility?: {
    role?: string;
    keyboard_navigable?: boolean;
    aria_label_required?: boolean;
  };
  renderer: string;
}
