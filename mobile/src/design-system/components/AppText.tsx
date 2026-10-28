import React from "react";
import {
  Text,
  type TextProps,
  type TextStyle,
} from "react-native";
import { useDesignTokens } from "../useDesignTokens";
import { typography } from "../tokens/typography";

type TypographyVariant = keyof typeof typography;
type SemanticTextColor =
  | "textPrimary"
  | "textSecondary"
  | "textMuted"
  | "textOnBrand";

type AppTextProps = TextProps & {
  variant?: TypographyVariant;
  color?: SemanticTextColor;
  children: React.ReactNode;
};

export function AppText({
  variant = "body",
  color = "textPrimary",
  style,
  children,
  ...props
}: AppTextProps) {
  const { colors } = useDesignTokens();

  const tokenStyle: TextStyle = {
    ...typography[variant],
    color: colors[color],
  };

  return (
    <Text
      {...props}
      allowFontScaling
      style={[tokenStyle, style]}
    >
      {children}
    </Text>
  );
}
