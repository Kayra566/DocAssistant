export type Role = "owner" | "admin" | "member" | "viewer";
export type Plan = "free" | "pro" | "business";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_verified: boolean;
  is_superuser: boolean;
  totp_enabled: boolean;
  created_at: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: Plan;
  created_at: string;
}

export interface Member {
  user_id: string;
  email: string;
  full_name: string | null;
  role: Role;
}

export interface RegisterResponse {
  user: User;
  organization_id: string;
  dev_verification_token: string | null;
}

export interface MessageResponse {
  message: string;
  dev_token?: string | null;
}

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  page_count: number;
  chunk_count: number;
  is_favorite: boolean;
  created_at: string;
}

export interface Citation {
  document_id: string;
  page: number;
  chunk_index: number;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: Citation[];
  tokens_used: number;
  cache_hit: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  tokens: number;
  created_at: string;
}

export interface Usage {
  plan: string;
  ai_tokens_used: number;
  ai_tokens_limit: number;
}

export type AIJobType =
  | "chat"
  | "summary"
  | "keypoints"
  | "quiz"
  | "translate"
  | "extract"
  | "compare";

export type AIJobStatus = "pending" | "running" | "done" | "failed";

export type SummaryLevel = "short" | "detailed" | "bullets" | "executive";
export type PromptPreset = "genel" | "hukuk" | "akademik" | "is";
export type QuizType = "multiple_choice" | "true_false" | "open_ended";

export interface QuizQuestion {
  type: QuizType;
  question: string;
  options: string[];
  answer: string;
  page?: number;
}

export interface AIJob {
  id: string;
  document_id: string | null;
  type: AIJobType;
  status: AIJobStatus;
  params: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  tokens_used: number;
  cache_hit: boolean;
  created_at: string;
}

export interface PresetInfo {
  key: string;
  description: string;
}

export interface PromptPresets {
  presets: PresetInfo[];
  summary_levels: PresetInfo[];
}

export type SubscriptionStatus =
  | "active"
  | "trialing"
  | "past_due"
  | "canceled"
  | "incomplete";

export interface PlanSpec {
  key: Plan;
  name: string;
  price_monthly: number;
  currency: string;
  documents: number;
  storage_mb: number;
  ai_requests: number;
  ai_tokens: number;
  features: string[];
}

export interface Subscription {
  id: string;
  organization_id: string;
  plan: Plan;
  status: SubscriptionStatus;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
}

export interface BillingUsage {
  plan: Plan;
  status: SubscriptionStatus;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
  documents_used: number;
  documents_limit: number;
  storage_bytes_used: number;
  storage_bytes_limit: number;
  ai_requests_used: number;
  ai_requests_limit: number;
  ai_tokens_used: number;
  ai_tokens_limit: number;
}

export type SharePermission = "view" | "download";

export interface ShareLink {
  id: string;
  document_id: string;
  permission: SharePermission;
  email: string | null;
  expires_at: string;
  revoked: boolean;
  view_count: number;
  last_accessed_at: string | null;
  created_at: string;
}

export interface ShareLinkCreated extends ShareLink {
  token: string;
  url: string;
}

export interface SharedDocument {
  filename: string;
  file_type: string;
  size_bytes: number;
  page_count: number;
  permission: SharePermission;
  can_download: boolean;
  expires_at: string;
  organization_name: string;
}

export interface DocumentComment {
  id: string;
  document_id: string;
  page: number | null;
  content: string;
  author_email: string | null;
  created_at: string;
}

export interface ActivityEntry {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  meta: Record<string, unknown> | null;
  actor_email: string | null;
  created_at: string;
}

export type ExportFormat = "pdf" | "docx" | "xlsx" | "md";
export type ExportStatus = "pending" | "running" | "done" | "failed";

export interface ExportJob {
  id: string;
  ai_job_id: string;
  format: ExportFormat;
  status: ExportStatus;
  filename: string;
  size_bytes: number;
  error: string | null;
  created_at: string;
}

export interface TrendPoint {
  date: string;
  documents: number;
  ai_jobs: number;
}

export interface DistributionItem {
  key: string;
  count: number;
}

export interface DashboardTotals {
  documents: number;
  ai_jobs: number;
  share_links: number;
  members: number;
}

export interface DashboardQuota {
  documents_used: number;
  documents_limit: number;
  storage_bytes_used: number;
  storage_bytes_limit: number;
  ai_requests_used: number;
  ai_requests_limit: number;
  ai_tokens_used: number;
  ai_tokens_limit: number;
}

export interface DashboardStats {
  plan: Plan;
  subscription_status: SubscriptionStatus;
  totals: DashboardTotals;
  quota: DashboardQuota;
  usage_trend: TrendPoint[];
  job_distribution: DistributionItem[];
  document_status: DistributionItem[];
}

export interface PlatformStats {
  users: number;
  verified_users: number;
  organizations: number;
  documents: number;
  ai_jobs: number;
  share_links: number;
  storage_bytes: number;
  plan_distribution: DistributionItem[];
}

export interface PlatformOrganization {
  id: string;
  name: string;
  slug: string;
  plan: Plan;
  documents: number;
  members: number;
  created_at: string;
}

export type NotificationType =
  | "welcome"
  | "invite"
  | "quota"
  | "billing"
  | "document"
  | "system";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

export interface FeatureFlags {
  flags: string[];
  environment: string;
  default_locale: string;
  sentry_enabled: boolean;
}

export interface ModelInfo {
  id: string;
  name: string;
  source: "ollama" | "file" | "builtin";
  ready: boolean;
  size_bytes: number;
  detail: string;
}

export interface ModelList {
  models: ModelInfo[];
  active_model_id: string;
  models_dir: string;
  ollama_available: boolean;
}

export interface IndexStatus {
  total_chunks: number;
  stale_chunks: number;
  dimension: number;
  provider: string;
  needs_reindex: boolean;
}
