import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { ProductReviewsContract } from "../types";

interface ProductReviewsProps {
  reviewsData: ProductReviewsContract;
  onRetry?: () => void;
  testID?: string;
}

export const ProductReviews: React.FC<ProductReviewsProps> = ({
  reviewsData,
  onRetry,
  testID = "product-reviews",
}) => {
  const { average_rating, total_reviews, distribution = [], reviews = [], state } = reviewsData;

  // Error state handling (Section 9.48)
  if (state === "error") {
    return (
      <View testID={testID} style={styles.errorContainer}>
        <Text style={styles.errorTitle}>Unable to load reviews</Text>
        {onRetry && (
          <TouchableOpacity
            testID={`${testID}-retry`}
            onPress={onRetry}
            style={styles.retryButton}
            accessibilityRole="button"
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  // Empty state handling (Section 9.23)
  if (total_reviews === 0 && reviews.length === 0) {
    return (
      <View testID={testID} style={styles.emptyContainer}>
        <Text style={styles.sectionHeading}>Customer Reviews</Text>
        <Text style={styles.emptyText}>No reviews yet. Be the first to review this product!</Text>
      </View>
    );
  }

  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.sectionHeading}>Customer Reviews ({total_reviews})</Text>

      {/* Rating Summary & Histogram (Section 9.21) */}
      <View style={styles.summaryRow}>
        <View style={styles.averageBox}>
          <Text testID={`${testID}-avg-score`} style={styles.averageScore}>
            {average_rating.toFixed(1)}
          </Text>
          <View style={styles.starsRow}>
            {[1, 2, 3, 4, 5].map((star) => (
              <Text key={`star-${star}`} style={styles.starIcon}>
                {star <= Math.round(average_rating) ? "★" : "☆"}
              </Text>
            ))}
          </View>
          <Text style={styles.totalReviewsLabel}>{total_reviews} ratings</Text>
        </View>

        {/* Histogram distribution */}
        <View style={styles.distributionBox}>
          {distribution.map((dist) => (
            <View key={`dist-${dist.stars}`} style={styles.histogramRow}>
              <Text style={styles.histStarLabel}>{dist.stars}★</Text>
              <View style={styles.histTrack}>
                <View
                  style={[
                    styles.histFill,
                    { width: `${Math.min(dist.percentage, 100)}%` },
                  ]}
                />
              </View>
              <Text style={styles.histCount}>{dist.count}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Review List & Cards (Section 9.22) */}
      <View style={styles.reviewsList}>
        {reviews.map((rev) => (
          <View key={rev.id} style={styles.reviewCard}>
            <View style={styles.cardHeader}>
              <View style={styles.authorRow}>
                <Text style={styles.authorName}>{rev.author}</Text>
                {rev.is_verified && (
                  <View style={styles.verifiedBadge}>
                    <Text style={styles.verifiedText}>✓ Verified Buyer</Text>
                  </View>
                )}
              </View>
              <Text style={styles.reviewDate}>{rev.date}</Text>
            </View>

            <View style={styles.ratingStars}>
              {[1, 2, 3, 4, 5].map((s) => (
                <Text key={`user-star-${s}`} style={styles.userStar}>
                  {s <= rev.rating ? "★" : "☆"}
                </Text>
              ))}
            </View>

            <Text style={styles.commentText}>{rev.comment}</Text>

            {rev.helpful_count !== undefined && rev.helpful_count > 0 && (
              <Text style={styles.helpfulText}>
                👍 Helpful ({rev.helpful_count})
              </Text>
            )}
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
    backgroundColor: "#ffffff",
  },
  sectionHeading: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
    marginBottom: 14,
  },
  summaryRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 20,
    marginBottom: 20,
  },
  averageBox: {
    alignItems: "center",
    justifyContent: "center",
  },
  averageScore: {
    fontSize: 34,
    fontWeight: "800",
    color: "#111111",
  },
  starsRow: {
    flexDirection: "row",
    gap: 2,
    marginVertical: 4,
  },
  starIcon: {
    fontSize: 15,
    color: "#d97706",
  },
  totalReviewsLabel: {
    fontSize: 12,
    color: "#777777",
  },
  distributionBox: {
    flex: 1,
    gap: 4,
  },
  histogramRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  histStarLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#555555",
    width: 22,
  },
  histTrack: {
    flex: 1,
    height: 6,
    backgroundColor: "#eeeeee",
    borderRadius: 3,
    overflow: "hidden",
  },
  histFill: {
    height: "100%",
    backgroundColor: "#d97706",
  },
  histCount: {
    fontSize: 11,
    color: "#888888",
    width: 24,
    textAlign: "right",
  },
  reviewsList: {
    gap: 14,
  },
  reviewCard: {
    padding: 12,
    backgroundColor: "#fafafa",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#eeeeee",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  authorRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  authorName: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111111",
  },
  verifiedBadge: {
    backgroundColor: "#e6f4ea",
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 3,
  },
  verifiedText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#137333",
  },
  reviewDate: {
    fontSize: 12,
    color: "#888888",
  },
  ratingStars: {
    flexDirection: "row",
    gap: 2,
    marginBottom: 6,
  },
  userStar: {
    fontSize: 13,
    color: "#d97706",
  },
  commentText: {
    fontSize: 13,
    color: "#333333",
    lineHeight: 18,
  },
  helpfulText: {
    fontSize: 11,
    color: "#666666",
    marginTop: 8,
  },
  emptyContainer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
  },
  emptyText: {
    fontSize: 13,
    color: "#888888",
    fontStyle: "italic",
  },
  errorContainer: {
    padding: 20,
    alignItems: "center",
    justifyContent: "center",
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
  },
  errorTitle: {
    fontSize: 14,
    color: "#a80000",
    marginBottom: 8,
  },
  retryButton: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    backgroundColor: "#eeeeee",
    borderRadius: 4,
  },
  retryButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#333333",
  },
});
