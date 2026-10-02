import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIHomeTemplateSpecContract } from "../types";
import { AIHero } from "../components/AIHero";
import { AIPromptInput } from "../components/AIPromptInput";
import { AIRecommendationCard } from "../components/AIRecommendationCard";

interface AIHomeTemplateProps {
  data: AIHomeTemplateSpecContract;
  onSubmitPrompt: (prompt: string) => void;
  onPressTask?: (actionId: string, targetId?: string | null) => void;
  onPressSession?: (sessionId: string) => void;
  onPressExploreRec?: (recId: string) => void;
  onPressActionRec?: (actionId: string, targetId?: string | null) => void;
  testID?: string;
}

export const AIHomeTemplate: React.FC<AIHomeTemplateProps> = ({
  data,
  onSubmitPrompt,
  onPressTask,
  onPressSession,
  onPressExploreRec,
  onPressActionRec,
  testID = "ai-home-screen",
}) => {
  const { hero_title, hero_subtitle, quick_prompts, suggested_tasks, recent_sessions, curated_recommendations } = data;

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <AIHero title={hero_title} subtitle={hero_subtitle} />

        <View style={styles.section}>
          <AIPromptInput
            quickPrompts={quick_prompts}
            onSubmit={onSubmitPrompt}
          />
        </View>

        {/* Suggested Tasks */}
        {suggested_tasks && suggested_tasks.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>SUGGESTED TASKS</Text>
            <View style={styles.taskGrid}>
              {suggested_tasks.map((task) => (
                <TouchableOpacity
                  key={task.action_id}
                  testID={`suggested-task-${task.action_id}`}
                  style={styles.taskCard}
                  onPress={() => onPressTask?.(task.action_id, task.target_id)}
                >
                  <Text style={styles.taskLabel}>{task.label}</Text>
                  <Text style={styles.taskArrow}>→</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Recent Sessions */}
        {recent_sessions && recent_sessions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>RECENT AI SESSIONS</Text>
            {recent_sessions.map((sess) => (
              <TouchableOpacity
                key={sess.id}
                testID={`recent-session-${sess.id}`}
                style={styles.sessionCard}
                onPress={() => onPressSession?.(sess.id)}
              >
                <Text style={styles.sessionTitle}>{sess.title}</Text>
                <Text style={styles.sessionMeta}>
                  {sess.messages?.length || 0} messages • Active session
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Curated Recommendations */}
        {curated_recommendations && curated_recommendations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>CURATED AI SUGGESTIONS</Text>
            {curated_recommendations.map((rec) => (
              <AIRecommendationCard
                key={rec.id}
                recommendation={rec}
                onPressExplore={onPressExploreRec}
                onPressAction={onPressActionRec}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FDFDFD",
  },
  content: {
    paddingBottom: 40,
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.1,
    marginBottom: 12,
  },
  taskGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  taskCard: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 14,
    marginBottom: 10,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  taskLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  taskArrow: {
    fontSize: 14,
    color: "#8E8E93",
  },
  sessionCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 14,
    marginBottom: 8,
  },
  sessionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 2,
  },
  sessionMeta: {
    fontSize: 11,
    color: "#8E8E93",
  },
});
