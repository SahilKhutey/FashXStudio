# Phase 08 Component Inventory

- **Catalog & Size Charts**: `SizeSystemDefinitionRecord`, `ProductSizeChartRecord`, `SizeChartRevisionRecord`, `SizeChartRowRecord`, `SizeChartMeasurementRecord`, `InventorySnapshotRecord`, `SizeChartQuarantineRecord`.
- **Shopper Fit Profile**: `ShopperProfile`, `ProfileMeasurement`, `ProfileMeasurementHistory`, `CategoryFitPreference`, `ProfileAuditEvent`.
- **Fit Recommendations**: `FitRecommendation`, `FitRecommendationEvidenceRecord`, `FitRecommendationCandidateRecord`, `FitFeedback`, `FitEvaluationCaseRecord`, `FitEvaluationRunRecord`.
- **Personalized Ranking**: `ProductFeedbackRecord`, `RankingPreferenceRecord`, `RankingEventRecord`, `RankingEvaluationRunRecord`, `PersonalizedRankingService`, `RankingCache`.
- **Feedback Loop**: `FeedbackEventRecord`, `FeedbackProcessingRecord`, `FeedbackOutboxRecord`, `ShopperProductReactionRecord`, `ShopperSavedProductRecord`, `ShopperConsentRecord`, `FeedbackConsentService`, `FeedbackIngestionService`, `FeedbackProcessor`.
- **Mobile**: `mobile/src/features/product-size/`, `mobile/src/features/fit-profile/`, `mobile/src/features/fit/`, `mobile/src/features/ranking/`, `mobile/src/features/feedback/`.
