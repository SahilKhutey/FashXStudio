import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { AIMessageContract } from "../types";

interface AIMessageViewProps {
  message: AIMessageContract;
  onPressAction?: (actionId: string, targetId?: string | null) => void;
  testID?: string;
}

export const AIMessageView: React.FC<AIMessageViewProps> = ({
  message,
  onPressAction,
  testID,
}) => {
  const isUser = message.role === "user";

  return (
    <View
      testID={testID || `ai-message-${message.id}`}
      style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}
    >
      <View style={styles.headerRow}>
        <Text style={[styles.roleTag, isUser ? styles.userRoleTag : styles.assistantRoleTag]}>
          {isUser ? "YOU" : "AI FASHION ASSISTANT"}
        </Text>
      </View>

      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
          {message.content}
        </Text>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <View style={styles.citationsContainer}>
            <Text style={styles.citationsHeader}>VERIFIED SOURCES</Text>
            {message.citations.map((cite, idx) => (
              <Text key={idx} style={styles.citationText}>
                • {cite.title} ({cite.source_type})
              </Text>
            ))}
          </View>
        )}
      </View>

      {/* Suggested Actions */}
      {message.suggested_actions && message.suggested_actions.length > 0 && (
        <View style={styles.actionsRail}>
          {message.suggested_actions.map((act) => (
            <TouchableOpacity
              key={act.action_id}
              testID={`message-action-${act.action_id}`}
              style={styles.actionButton}
              onPress={() => onPressAction?.(act.action_id, act.target_id)}
            >
              <Text style={styles.actionButtonText}>{act.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  userContainer: {
    alignItems: "flex-end",
  },
  assistantContainer: {
    alignItems: "flex-start",
  },
  headerRow: {
    marginBottom: 4,
  },
  roleTag: {
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  userRoleTag: {
    color: "#8E8E93",
  },
  assistantRoleTag: {
    color: "#5856D6",
  },
  bubble: {
    borderRadius: 14,
    padding: 12,
    maxWidth: "85%",
  },
  userBubble: {
    backgroundColor: "#1C1C1E",
    borderBottomRightRadius: 2,
  },
  assistantBubble: {
    backgroundColor: "#F2F2F7",
    borderBottomLeftRadius: 2,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: "#FFFFFF",
  },
  assistantText: {
    color: "#1C1C1E",
  },
  citationsContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  citationsHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  citationText: {
    fontSize: 11,
    color: "#636366",
  },
  actionsRail: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#D1D1D6",
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#007AFF",
  },
});
