/**
 * ResponsiveSheet — Adaptive Bottom Sheet / Modal (Section 14.53 - 14.55).
 *
 * Renders as a bottom sheet with drag handle on compact viewports,
 * and as a centered floating dialog on adaptive/expanded viewports.
 */

import React, { ReactNode } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TouchableWithoutFeedback,
  ScrollView,
} from 'react-native';
import { useResponsive } from '../hooks/useResponsive';

interface ResponsiveSheetProps {
  visible: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  maxHeightRatio?: number;
}

export const ResponsiveSheet: React.FC<ResponsiveSheetProps> = ({
  visible,
  title,
  onClose,
  children,
  maxHeightRatio = 0.85,
}) => {
  const { isCompact, height } = useResponsive();

  if (!visible) return null;

  return (
    <Modal
      transparent
      visible={visible}
      animationType={isCompact ? 'slide' : 'fade'}
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={[styles.backdrop, isCompact ? styles.backdropBottom : styles.backdropCenter]}>
          <TouchableWithoutFeedback>
            <View
              style={[
                isCompact ? styles.bottomSheetContainer : styles.modalContainer,
                { maxHeight: height * maxHeightRatio },
              ]}
            >
              {/* Mobile Drag Handle */}
              {isCompact && <View style={styles.dragHandle} />}

              {/* Header */}
              <View style={styles.sheetHeader}>
                <Text style={styles.sheetTitle}>{title}</Text>
                <TouchableOpacity
                  onPress={onClose}
                  accessibilityLabel="Close dialog"
                  accessibilityRole="button"
                  style={styles.closeButton}
                >
                  <Text style={styles.closeText}>✕</Text>
                </TouchableOpacity>
              </View>

              {/* Body */}
              <ScrollView style={styles.sheetBody}>{children}</ScrollView>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  backdropBottom: {
    justifyContent: 'flex-end',
  },
  backdropCenter: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  bottomSheetContainer: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 12,
    paddingBottom: 24,
    paddingHorizontal: 20,
  },
  modalContainer: {
    width: '100%',
    maxWidth: 540,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 10,
  },
  dragHandle: {
    width: 40,
    height: 4,
    backgroundColor: '#D1D5DB',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 12,
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  closeButton: {
    padding: 8,
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '600',
  },
  sheetBody: {
    paddingTop: 16,
  },
});
