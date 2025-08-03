/**
 * Interview scheduling related types
 */

export interface InterviewRequest {
  candidate_name: string;
  candidate_email: string;
  interviewer_names: string[];
  interviewer_emails: string[];
  duration_minutes?: number;
  preferred_dates?: string[];
  auto_select?: boolean;
}

export interface InterviewResponse {
  request_id: string;
  status: 'scheduled' | 'pending' | 'failed' | 'cancelled';
  scheduled_time?: string;
  meet_link?: string;
  calendar_event_id?: string;
  email_message_id?: string;
  available_slots?: TimeSlot[];
  error?: string;
}

export interface TimeSlot {
  start: string;
  end: string;
  attendees: string[];
}

export interface AvailableSlotsResponse {
  available_slots: TimeSlot[];
}