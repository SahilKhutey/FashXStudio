/**
 * FashXStudio — Modal Component (Phase 05 - Level 2 Core UI)
 *
 * Accessible modal dialog with backdrop scrim, focus trapping,
 * title header, close trigger, and action footer.
 * Consumes Phase 02 elevation, zIndex, and spacing tokens.
 */

import React, { useEffect } from 'react';
import {
  BackHandler,
  Modal as RNModal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  elevationShadows,
  radiusScale,
  spacingScale,
  typeScale,
  zIndexScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { ModalProps } from './types';

export function Modal({
  visible,
  title,
  children,
  footerActions,
  size = 'md',
  isDismissible = true,
  onClose,
  hasScrim = true,
  testID,
}: ModalProps) {
  useEffect(() => {
    if (!visible) return;

    const backHandler = BackHandler.addEventListener(
      'hardwareBackPress',
      () => {
        if (isDismissible) {
          onClose();
          return true;
        }
        return false;
      },
    );

    return () => backHandler.remove();
  }, [visible, isDismissible, onClose]);

  const getWidth = () => {
    switch (size) {
      case 'sm':
        return 320;
      case 'lg':
        return 560;
      case 'md':
      default:
        return 440;
    }
  };

  return (
    <RNModal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={isDismissible ? onClose : undefined}
      accessibilityViewIsModal={true}
      testID={testID}
    >
      <View style={styles.overlay}>
        {hasScrim && (
          <Pressable
            style={styles.scrim}
            onPress={isDismissible ? onClose : undefined}
            accessibilityLabel="Close modal backdrop"
          />
        )}

        <View
          style={[
            styles.dialog,
            { maxWidth: getWidth(), width: '90%' },
            elevationShadows[5],
          ]}
          accessibilityRole="alert"
        >
          {title && (
            <View style={styles.header}>
              <Text style={styles.title} numberOfLines={1}>
                {title}
              </Text>
              {isDismissible && (
                <Pressable
                  onPress={onClose}
                  style={styles.closeButton}
                  accessibilityRole="button"
                  accessibilityLabel="Close modal"
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={styles.closeIcon}>✕</Text>
                </Pressable>
              )}
            </View>
          )}

          <ScrollView style={styles.body}>{children}</ScrollView>

          {footerActions && (
            <View style={styles.footer}>{footerActions}</View>
          )}
        </View>
      </View>
    </RNModal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: zIndexScale.modal,
  },
  scrim: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  dialog: {
    backgroundColor: lightSemanticSurfaces.primary,
    borderRadius: radiusScale.lg,
    maxHeight: '85%',
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacingScale.space4,
    paddingVertical: spacingScale.space3,
    borderBottomWidth: 1,
    borderBottomColor: lightSemanticBorders.subtle,
  },
  title: {
    fontSize: typeScale.headingM.fontSize,
    lineHeight: typeScale.headingM.lineHeight,
    fontWeight: '600',
    color: lightSemanticContent.primary,
    flex: 1,
  },
  closeButton: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeIcon: {
    fontSize: 16,
    color: lightSemanticContent.secondary,
  },
  body: {
    padding: spacingScale.space4,
  },
  footer: {
    paddingHorizontal: spacingScale.space4,
    paddingVertical: spacingScale.space3,
    borderTopWidth: 1,
    borderTopColor: lightSemanticBorders.subtle,
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacingScale.space2,
  },
});
