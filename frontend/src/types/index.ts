export interface Session {
  session_id: string;
  original_video_url: string | null;
  raw_seadance_url: string | null;
  conditioned_seadance_url: string | null;
  joint_data: Record<string, unknown> | null;
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
