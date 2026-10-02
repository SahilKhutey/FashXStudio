/**
 * FashXStudio Production Visual Integration, Verification & Release Contracts.
 * Phase 16: VD-16 — FINAL.
 */

export type ProductionLayer =
  | 'layer_0_platform'
  | 'layer_1_shell'
  | 'layer_2_design_system'
  | 'layer_3_features'
  | 'layer_4_templates'
  | 'layer_5_screens'
  | 'layer_6_services'
  | 'layer_7_analytics'
  | 'layer_8_qa';

export type ReleaseGateStatus = 'passed' | 'failed' | 'pending' | 'warning' | 'blocked';

export type ReleaseEnvironment = 'development' | 'staging' | 'production';

export type QualityCategory =
  | 'foundation'
  | 'shell'
  | 'components'
  | 'fashion'
  | 'shopping'
  | 'discovery'
  | 'styling'
  | 'geography'
  | 'ai'
  | 'personal'
  | 'responsive'
  | 'accessibility'
  | 'qa';

export type GoldenArtifactType = 'screen' | 'component';

export interface ScreenRegistryEntryContract {
  screen_id: string;
  route: string;
  title: string;
  template: string;
  feature: string;
  accessibility_role: string;
  analytics_tag: string;
  dependencies: string[];
  is_production_ready: boolean;
}

export interface NavigationRegistryEntryContract {
  route: string;
  label: string;
  icon: string;
  group: string;
  visibility: string;
  permissions: string[];
  screen_id: string;
}

export interface TokenValidationRequestContract {
  token_name: string;
  token_category: string;
  primitive_ref: string;
  semantic_usage: string;
  theme?: string;
}

export interface TokenValidationReportContract {
  token_name: string;
  is_valid: boolean;
  resolved_value?: string | null;
  errors: string[];
  warnings: string[];
  hierarchy_valid: boolean;
}

export interface ReleaseGateResultContract {
  gate_name: string;
  status: ReleaseGateStatus;
  score: number;
  passed: boolean;
  violations: string[];
  timestamp: string;
}

export interface VisualReleaseGateAuditRequest {
  release_version: string;
  environment?: ReleaseEnvironment;
  target_screens?: string[];
  include_e2e?: boolean;
  include_a11y?: boolean;
}

export interface VisualChecklistItemContract {
  item_id: string;
  category: QualityCategory;
  title: string;
  description: string;
  is_verified: boolean;
  verification_method: string;
}

export interface EndToEndJourneySpecContract {
  journey_id: string;
  name: string;
  steps: string[];
  status: ReleaseGateStatus;
  verified_at: string;
}

export interface GoldenArtifactContract {
  id: string;
  name: string;
  artifact_type: GoldenArtifactType;
  baseline_reference: string;
  match_threshold: number;
  status: ReleaseGateStatus;
}

export interface ProductionReleaseReportContract {
  release_version: string;
  environment: ReleaseEnvironment;
  overall_passed: boolean;
  gates: ReleaseGateResultContract[];
  checklist_summary: Record<string, number>;
  golden_screens_count: number;
  golden_components_count: number;
  timestamp: string;
}

export interface VisualTrackStatusContract {
  phase_statuses: Record<string, string>;
  visual_design_architecture_pct: number;
  visual_specification_pct: number;
  actual_repository_implementation_pct: number;
  total_phases: number;
  status_message: string;
}
