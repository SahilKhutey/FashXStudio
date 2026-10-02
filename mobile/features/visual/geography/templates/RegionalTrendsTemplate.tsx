import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { RegionalTrendsTemplateSpecContract } from "../types";
import { RegionalTrendCard } from "../components/RegionalTrendCard";

interface RegionalTrendsTemplateProps {
  data: RegionalTrendsTemplateSpecContract;
  onPressTrend?: (trendId: string) => void;
  testID?: string;
}

export const RegionalTrendsTemplate: React.FC<RegionalTrendsTemplateProps> = ({
  data,
  onPressTrend,
  testID = "regional-trends-screen",
}) => {
  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.tag}>REGIONAL FASHION PULSE</Text>
        <Text style={styles.title}>{data.region.name} Trends</Text>
        <Text style={styles.subtitle}>
          Active movements, cultural influences, and textile adaptations in {data.region.name}.
        </Text>
      </View>

      <View style={styles.trendsList}>
        {data.trends.map((trend) => (
          <RegionalTrendCard
            key={trend.id}
            trend={trend}
            onPressTrend={onPressTrend}
          />
        ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  tag: {
    fontSize: 10,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
    marginTop: 2,
  },
  subtitle: {
    fontSize: 13,
    color: "#4b5563",
    marginTop: 4,
    lineHeight: 18,
  },
  trendsList: {
    padding: 16,
  },
});
