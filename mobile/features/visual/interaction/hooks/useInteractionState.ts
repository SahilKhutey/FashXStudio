/**
 * FashXStudio useInteractionState Hook — Version 1.
 *
 * Implements the component interaction state precedence machine (Section 15.3 - 15.5).
 */

import { useState, useCallback } from 'react';
import { InteractionState } from '../types';

interface UseInteractionStateProps {
  isDisabled?: boolean;
  isLoading?: boolean;
  isError?: boolean;
  isSelected?: boolean;
  isUnavailable?: boolean;
}

export interface UseInteractionStateResult {
  activeState: InteractionState;
  isHovered: boolean;
  isFocused: boolean;
  isPressed: boolean;
  onHoverIn: () => void;
  onHoverOut: () => void;
  onFocus: () => void;
  onBlur: () => void;
  onPressIn: () => void;
  onPressOut: () => void;
  isInteractive: boolean;
  ariaDisabled: boolean;
  ariaBusy: boolean;
  ariaInvalid: boolean;
}

export function useInteractionState(props: UseInteractionStateProps = {}): UseInteractionStateResult {
  const {
    isDisabled = false,
    isLoading = false,
    isError = false,
    isSelected = false,
    isUnavailable = false,
  } = props;

  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isPressed, setIsPressed] = useState(false);

  const onHoverIn = useCallback(() => setIsHovered(true), []);
  const onHoverOut = useCallback(() => setIsHovered(false), []);
  const onFocus = useCallback(() => setIsFocused(true), []);
  const onBlur = useCallback(() => setIsFocused(false), []);
  const onPressIn = useCallback(() => setIsPressed(true), []);
  const onPressOut = useCallback(() => setIsPressed(false), []);

  // Strict Precedence (Section 15.5): Error > Unavailable > Disabled > Loading > Selected > Pressed > Focus > Hover > Rest
  let activeState: InteractionState = 'rest';

  if (isError) {
    activeState = 'error';
  } else if (isUnavailable) {
    activeState = 'unavailable';
  } else if (isDisabled) {
    activeState = 'disabled';
  } else if (isLoading) {
    activeState = 'loading';
  } else if (isSelected) {
    activeState = 'selected';
  } else if (isPressed) {
    activeState = 'active';
  } else if (isFocused) {
    activeState = 'focus';
  } else if (isHovered) {
    activeState = 'hover';
  } else {
    activeState = 'rest';
  }

  const isInteractive = !isDisabled && !isLoading && !isUnavailable;

  return {
    activeState,
    isHovered,
    isFocused,
    isPressed,
    onHoverIn,
    onHoverOut,
    onFocus,
    onBlur,
    onPressIn,
    onPressOut,
    isInteractive,
    ariaDisabled: isDisabled || isUnavailable,
    ariaBusy: isLoading,
    ariaInvalid: isError,
  };
}
