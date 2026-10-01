/**
 * FashXStudio — Component Framework Types (Phase 05)
 *
 * TypeScript contracts mirroring schemas/visual/components.py.
 * Covers Level 1 (Primitives) and Level 2 (Core UI) components.
 */

export type ComponentTaxonomy =
  | 'level_1_primitive'
  | 'level_2_core_ui'
  | 'level_3_domain'
  | 'level_4_feature';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'ghost'
  | 'destructive';

export type ComponentSize = 'sm' | 'md' | 'lg';

export type InputType =
  | 'text'
  | 'search'
  | 'email'
  | 'password'
  | 'number'
  | 'phone';

export type BadgeVariant =
  | 'default'
  | 'brand'
  | 'success'
  | 'warning'
  | 'error'
  | 'accent'
  | 'neutral'
  | 'outline';

export type CardVariant = 'elevated' | 'outlined' | 'filled';

export type TypographyRole =
  | 'display_xl'
  | 'display_l'
  | 'display_m'
  | 'heading_xl'
  | 'heading_l'
  | 'heading_m'
  | 'heading_s'
  | 'heading_xs'
  | 'body_l'
  | 'body_m'
  | 'body_s'
  | 'label_l'
  | 'label_m'
  | 'label_s'
  | 'caption'
  | 'overline';

export type SkeletonShape = 'rectangle' | 'rounded' | 'circle' | 'text';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ComponentSize;
  label: string;
  onPress?: () => void;
  icon?: string;
  iconPosition?: 'left' | 'right';
  isLoading?: boolean;
  isDisabled?: boolean;
  isFullWidth?: boolean;
  accessibilityLabel?: string;
  testID?: string;
}

export interface InputProps {
  inputType?: InputType;
  value?: string;
  onChangeText?: (text: string) => void;
  label?: string;
  placeholder?: string;
  helperText?: string;
  errorText?: string;
  isDisabled?: boolean;
  isReadOnly?: boolean;
  isRequired?: boolean;
  leadingIcon?: string;
  trailingIcon?: string;
  showClearButton?: boolean;
  onClear?: () => void;
  accessibilityLabel?: string;
  testID?: string;
}

export interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: ComponentSize;
  isPill?: boolean;
  isDismissible?: boolean;
  onDismiss?: () => void;
  icon?: string;
  testID?: string;
}

export interface TypographyProps {
  role?: TypographyRole;
  children: React.ReactNode;
  color?: string;
  align?: 'left' | 'center' | 'right' | 'justify';
  maxLines?: number;
  accessibilityRole?: 'header' | 'text';
  testID?: string;
}

export interface SkeletonProps {
  shape?: SkeletonShape;
  width?: number | string;
  height?: number | string;
  borderRadius?: number;
  isAnimated?: boolean;
  testID?: string;
}

export interface CardProps {
  children: React.ReactNode;
  variant?: CardVariant;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  isClickable?: boolean;
  isHoverable?: boolean;
  onPress?: () => void;
  accessibilityLabel?: string;
  testID?: string;
}

export interface ModalProps {
  visible: boolean;
  title?: string;
  children: React.ReactNode;
  footerActions?: React.ReactNode;
  size?: ComponentSize;
  isDismissible?: boolean;
  onClose: () => void;
  hasScrim?: boolean;
  testID?: string;
}

export interface RatingProps {
  value: number;
  maxStars?: number;
  allowHalf?: boolean;
  showScore?: boolean;
  isReadOnly?: boolean;
  onChange?: (val: number) => void;
  ratingCount?: number;
  testID?: string;
}

export interface SegmentedControlOption {
  id: string;
  label: string;
  icon?: string;
  badge?: string;
}

export interface SegmentedControlProps {
  options: SegmentedControlOption[];
  selectedId: string;
  onSelect: (id: string) => void;
  size?: ComponentSize;
  isFullWidth?: boolean;
  testID?: string;
}

export interface FormFieldProps {
  fieldId: string;
  label: string;
  children: React.ReactNode;
  isRequired?: boolean;
  helperText?: string;
  errorText?: string;
  state?: 'default' | 'focus' | 'error' | 'success' | 'disabled';
  testID?: string;
}
