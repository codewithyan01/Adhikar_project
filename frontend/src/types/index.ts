export type VerdictType = 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'UNSURE' | 'APPLICABLE' | 'NOT_APPLICABLE';

export interface UserProfile {
  age?: number;
  state?: string;
  occupation?: string;
  income?: number;
  category?: string;
  gender?: string;
  dispute_description?: string;
  grievance?: string;
  name?: string;
  address?: string;
  [key: string]: any;
}

export interface MatchedScheme {
  id: string;
  name: string;
  verdict: VerdictType;
  cited_clause: string;
  reasoning: string;
  caveat?: string | null;
  benefits: string;
  application_process?: string | null;
  source_url: string;
  structured_slots?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  status?: string;
}

export interface RTIDepartment {
  id: string;
  name: string;
  jurisdiction: string;
  designation_pio: string;
  common_issues: string[];
  keywords: string[];
  fee_details: string;
}

export interface RTIRoutingResult {
  primary_department: RTIDepartment;
  confidence_score: number;
  requires_confirmation: boolean;
  candidate_departments: RTIDepartment[];
  explanation: string;
}

export interface RTIDraftResult {
  department: RTIDepartment;
  applicant_details: Record<string, any>;
  subject_line: string;
  framed_questions: string[];
  statutory_declaration: string;
  fee_guidance: string;
  filing_instructions: string[];
}

export interface RightsArticle {
  id: string;
  category: 'consumer' | 'tenant' | 'workplace' | string;
  title: string;
  act_reference: string;
  source_url: string;
  authority: string;
  caveat?: string | null;
  content: string;
  key_remedies: string;
}

export interface RightsExplainerResult {
  rights_id: string;
  title: string;
  category: string;
  act_reference: string;
  authority: string;
  source_url: string;
  verdict: string;
  cited_clause: string;
  explanation: string;
  key_remedies: string;
  caveat?: string | null;
  legal_aid_referral?: string | null;
}

export type ViewMode = 'schemes' | 'rights' | 'document' | 'rti';
