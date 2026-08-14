export type UserRole =
  | "ORGANIZATION_ADMIN"
  | "RECRUITER"
  | "HIRING_MANAGER"
  | "CANDIDATE";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
};

export type JobStatus = "DRAFT" | "PUBLISHED" | "CLOSED" | "ARCHIVED";

export type Job = {
  id: string;
  title: string;
  description: string;
  location: string | null;
  employment_type: string | null;
  min_experience_years: number | null;
  status: JobStatus;
  is_public: boolean;
  created_at: string;
  required_skills: string[];
  preferred_skills: string[];
};

export type Application = {
  id: string;
  job_id: string;
  candidate_id: string;
  resume_id: string;
  status: string;
  submitted_at: string;
  candidate: {
    id: string;
    full_name: string;
    email: string;
    phone: string | null;
    location: string | null;
    summary: string | null;
    created_at: string;
  };
  resume: {
    id: string;
    original_filename: string;
    file_type: string;
    mime_type: string;
    file_size: number;
    status: string;
    created_at: string;
  };
};

export type ScreeningRecommendation = "STRONG_MATCH" | "REVIEW" | "LOW_MATCH";

export type ScreeningResult = {
  id: string;
  application_id: string;
  overall_score: number;
  keyword_score: number;
  semantic_score: number;
  experience_score: number;
  completeness_score: number;
  recommendation: ScreeningRecommendation;
  provider: string;
  model_name: string;
  matched_skills: string[];
  missing_required_skills: string[];
  matched_preferred_skills: string[];
  strengths: string[];
  concerns: string[];
  improvement_suggestions: string[];
  explanation: string;
  resume_sections: Record<string, string>;
  processing_ms: number | null;
  created_at: string;
};

export type ScreeningListItem = {
  application_id: string;
  candidate_name: string;
  job_title: string;
  submitted_at: string;
  overall_score: number | null;
  recommendation: ScreeningRecommendation | null;
  application_status: string;
};

export type AnalyticsOverview = {
  total_jobs: number;
  total_applications: number;
  screened_applications: number;
  average_score: number;
  recommendations: {
    strong_match: number;
    review: number;
    low_match: number;
  };
};

export type ScreeningQueueStats = Record<string, number>;

export type AuditEvent = {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  actor_user_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
};
