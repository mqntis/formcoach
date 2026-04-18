export interface Session {
  session_id: string;
  original_video_url: string | null;
  raw_seadance_url: string | null;
  conditioned_seadance_url: string | null;
  joint_data: unknown[] | null;
  correction_text: string | null;
  verified_correction: boolean;
  phone_number: string | null;
  created_at: string;
}

export interface UploadUrlResponse {
  upload_url: string;
  object_id: string;
  expires_in: number;
}

export interface ExtractResult {
  object_id: string;
  frame_count: number;
  joint_data: unknown[];
}

export interface Analysis {
  movement_type: string;
  errors: string[];
  correction_description: string;
}

export interface VerifyResult {
  verified: boolean;
  issues_found: string[];
  final_correction: string;
}

export interface GenerateResult {
  session_id: string;
  before_url: string;
  after_url: string;
}
