/**
 * LiveAnnouncement — Accessible screen reader live region wrapper (Section 15.15 & 15.79).
 *
 * Visually hides announcement text while guaranteeing delivery to screen readers.
 */

import React, { useEffect } from 'react';
import { View, Text, StyleSheet, AccessibilityInfo } from 'react-native';

interface LiveAnnouncementProps {
  message: string;
  politeness?: 'polite' | 'assertive';
}

export const LiveAnnouncement: React.FC<LiveAnnouncementProps> = ({
  message,
  politeness = 'polite',
}) => {
  useEffect(() => {
    if (message) {
      AccessibilityInfo.announceForAccessibility(message);
    }
  }, [message]);

  if (!message) return null;

  return (
    <View style={styles.srOnly} accessibilityLiveRegion={politeness}>
      <Text>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  srOnly: {
    position: 'absolute',
    width: 1,
    height: 1,
    padding: 0,
    margin: -1,
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    borderWidth: 0,
  },
});
