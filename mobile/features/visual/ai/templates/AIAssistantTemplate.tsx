import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { AIAssistantTemplateSpecContract } from "../types";
import { AIMessageView } from "../components/AIMessageView";
import { AIContextChips } from "../components/AIContextChips";
import { AIPromptInput } from "../components/AIPromptInput";

interface AIAssistantTemplateProps {
  data: AIAssistantTemplateSpecContract;
  onSubmitPrompt: (prompt: string) => void;
  onPressAction?: (actionId: string, targetId?: string | null) => void;
  onRemoveContext?: (key: string) => void;
  onEditContext?: () => void;
  testID?: string;
}

export const AIAssistantTemplate: React.FC<AIAssistantTemplateProps> = ({
  data,
  onSubmitPrompt,
  onPressAction,
  onRemoveContext,
  onEditContext,
  testID = "ai-assistant-screen",
}) => {
  const { session, active_context, suggested_prompts } = data;

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTag}>SESSION</Text>
        <Text style={styles.headerTitle}>{session.title}</Text>
      </View>

      {active_context && active_context.length > 0 && (
        <AIContextChips
          contextItems={active_context}
          onRemoveItem={onRemoveContext}
          onEditContext={onEditContext}
        />
      )}

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.messagesList}
      >
        {session.messages && session.messages.length > 0 ? (
          session.messages.map((msg) => (
            <AIMessageView
              key={msg.id}
              message={msg}
              onPressAction={onPressAction}
            />
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>What can I help you explore?</Text>
            <Text style={styles.emptySubtitle}>
              Ask about styles, outfits, sizing, or finding products in our catalog.
            </Text>
          </View>
        )}
      </ScrollView>

      <AIPromptInput
        quickPrompts={suggested_prompts}
        onSubmit={onSubmitPrompt}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FDFDFD",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    backgroundColor: "#FFFFFF",
  },
  headerTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  messagesList: {
    paddingVertical: 12,
  },
  emptyState: {
    padding: 32,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#8E8E93",
    textAlign: "center",
    lineHeight: 18,
  },
});
