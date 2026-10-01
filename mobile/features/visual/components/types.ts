/**
 * FashXStudio — Component Framework Types (Phase 05 - Complete System)
 *
 * TypeScript contracts mirroring schemas/visual/components.py across all 5 layers:
 * L0 Tokens, L1 Primitives, L2 Core UI, L3 Composites, L4 Patterns.
 */

export type ComponentTaxonomy =
  | 'level_0_tokens'
  | 'level_1_primitive'
  | 'level_2_core_ui'
  | 'level_3_composite'
  | 'level_4_pattern';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'tertiary'
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
  | 'phone'
  | 'textarea';

export type BadgeVariant =
  | 'default'
  | 'brand'
  | 'success'
  | 'warning'
  | 'error'
  | 'accent'
  | 'neutral'
  | 'outline'
  | 'info';

export type CardVariant =
  | 'default'
  | 'elevated'
  | 'outlined'
  | 'filled'
  | 'interactive'
  | 'compact'
  | 'media';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export type ProgressVariant = 'linear' | 'circular' | 'stepper';

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

// ---------------------------------------------------------------------------
// L1: Primitives
// ---------------------------------------------------------------------------

export interface BoxProps {
  children?: React.ReactNode;
  padding?: number | string;
  margin?: number | string;
  backgroundColor?: string;
  borderRadius?: number;
  borderColor?: string;
  borderWidth?: number;
  style?: any;
  testID?: string;
}

export interface StackProps {
  children: React.ReactNode;
  gap?: number;
  align?: 'stretch' | 'flex-start' | 'center' | 'flex-end';
  reversed?: boolean;
  style?: any;
  testID?: string;
}

export interface InlineProps {
  children: React.ReactNode;
  gap?: number;
  align?: 'center' | 'flex-start' | 'flex-end' | 'baseline';
  justify?: 'flex-start' | 'center' | 'flex-end' | 'space-between';
  wrap?: boolean;
  style?: any;
  testID?: string;
}

export interface GridProps {
  children: React.ReactNode;
  columns?: number;
  gutter?: number;
  style?: any;
  testID?: string;
}

export interface ContainerProps {
  children: React.ReactNode;
  maxWidth?: number;
  paddingHorizontal?: number;
  centered?: boolean;
  style?: any;
  testID?: string;
}

export interface CenterProps {
  children: React.ReactNode;
  style?: any;
  testID?: string;
}

// ---------------------------------------------------------------------------
// L2: Core Components
// ---------------------------------------------------------------------------

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

export interface IconButtonProps {
  icon: string;
  accessibilityLabel: string;
  onPress?: () => void;
  size?: ComponentSize;
  variant?: ButtonVariant;
  isDisabled?: boolean;
  testID?: string;
}

export interface LinkProps {
  href: string;
  label: string;
  onPress?: () => void;
  isExternal?: boolean;
  variant?: 'default' | 'subtle' | 'underline';
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

export interface ChipProps {
  label: string;
  isSelected?: boolean;
  isRemovable?: boolean;
  onPress?: () => void;
  onRemove?: () => void;
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

export interface AvatarProps {
  imageUri?: string;
  initials?: string;
  size?: ComponentSize;
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

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  isDismissible?: boolean;
  onDismiss?: () => void;
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

export interface PriceProps {
  amount: number;
  originalAmount?: number;
  currencySymbol?: string;
  discountPercentage?: number;
  size?: ComponentSize;
  testID?: string;
}

export interface QuantityControlProps {
  value: number;
  onChange: (val: number) => void;
  minValue?: number;
  maxValue?: number;
  isDisabled?: boolean;
  testID?: string;
}

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showPrevNext?: boolean;
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

export interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  testID?: string;
}

export interface ErrorStateProps {
  title?: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
  recoveryLabel?: string;
  onRecovery?: () => void;
  testID?: string;
}

// ---------------------------------------------------------------------------
// L3: Composite Components
// ---------------------------------------------------------------------------

export interface ProductCardProps {
  productId: string;
  title: string;
  brand: string;
  imageUri: string;
  price: number;
  originalPrice?: number;
  currencySymbol?: string;
  rating?: number;
  isSaved?: boolean;
  onPress?: () => void;
  onSaveToggle?: () => void;
  badge?: string;
  testID?: string;
}

export interface FashionCardProps {
  storyId: string;
  title: string;
  category: string;
  imageUri: string;
  description?: string;
  onPress?: () => void;
  testID?: string;
}

export interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChangeText?: (text: string) => void;
  onSubmit?: () => void;
  onFilterPress?: () => void;
  showFilterButton?: boolean;
  testID?: string;
}

export interface FilterBarProps {
  activeChips: { id: string; label: string }[];
  onRemoveChip: (id: string) => void;
  onClearAll?: () => void;
  filterCount?: number;
  onOpenFilters?: () => void;
  testID?: string;
}
