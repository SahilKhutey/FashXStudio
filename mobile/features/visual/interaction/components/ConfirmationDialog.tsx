/**
 * ConfirmationDialog — Destructive action confirmation modal (Section 15.56 & 15.57).
 *
 * Enforces explicit consequence wording, focus lock, and accessible dismissal.
 */

import React from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TouchableWithoutFeedback,
} from 'react-native';

interface ConfirmationDialogProps {
  visible: boolean;
  title: string;
  consequenceMessage: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isDestructive?: boolean;
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  visible,
  title,
  consequenceMessage,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  isDestructive = true,
}) => {
  if (!visible) return null;

  return (
    <Modal
      transparent
      visible={visible}
      animationType="fade"
      onRequestClose={onCancel}
    >
      <TouchableWithoutFeedback onPress={onCancel}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View style={styles.dialogCard} accessibilityRole="alertdialog">
              <Text style={styles.titleText}>{title}</Text>
              <Text style={styles.messageText}>{consequenceMessage}</Text>

              <View style={styles.actionsRow}>
                <TouchableOpacity
                  onPress={onCancel}
                  style={styles.cancelButton}
                  accessibilityRole="button"
                  accessibilityLabel={cancelLabel}
                >
                  <Text style={styles.cancelText}>{cancelLabel}</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={onConfirm}
                  style={[
                    styles.confirmButton,
                    isDestructive ? styles.destructiveButton : styles.primaryButton,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={confirmLabel}
                >
                  <Text style={styles.confirmText}>{confirmLabel}</Text>
                </TouchableOpacity>
              </View>
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
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  dialogCard: {
    width: '100%',
    maxWidth: 440,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
  },
  titleText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  messageText: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 20,
    marginTop: 8,
    marginBottom: 24,
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelButton: {
    minHeight: 44,
    paddingHorizontal: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  cancelText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  confirmButton: {
    minHeight: 44,
    paddingHorizontal: 18,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
  },
  destructiveButton: {
    backgroundColor: '#DC2626',
  },
  primaryButton: {
    backgroundColor: '#111827',
  },
  confirmText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
