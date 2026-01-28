// User types
export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: string;
  created_at: string;
  updated_at: string;
}

// Organization types
export interface Organization {
  id: string;
  name: string;
  industry: string | null;
  size: string | null;
  website: string | null;
  primary_contact_id: string | null;
  billing_contact_id: string | null;
  tags: string[];
  segment: string | null;
  source: string | null;
  lifetime_value: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationWithContacts extends Organization {
  primary_contact: ContactSummary | null;
  billing_contact: ContactSummary | null;
  contact_count: number;
}

// Contact types
export type ContactType = "lead" | "client" | "past_client" | "partner";
export type CoachingType = "executive" | "life" | "group";

export interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  organization_id: string | null;
  role: string | null;
  title: string | null;
  contact_type: ContactType;
  coaching_type: CoachingType | null;
  tags: string[];
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactSummary {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
}

export interface ContactWithOrganization extends Contact {
  organization: OrganizationSummary | null;
}

export interface OrganizationSummary {
  id: string;
  name: string;
}

// Interaction types
export type InteractionType = "email" | "call" | "meeting" | "note";
export type Direction = "inbound" | "outbound";

export interface Interaction {
  id: string;
  contact_id: string;
  interaction_type: InteractionType;
  subject: string | null;
  content: string | null;
  direction: Direction | null;
  gmail_message_id: string | null;
  created_at: string;
  created_by: string | null;
}

// List response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface InteractionList {
  items: Interaction[];
  total: number;
}

// Form types
export interface ContactFormData {
  first_name: string;
  last_name?: string;
  email?: string;
  phone?: string;
  organization_id?: string;
  role?: string;
  title?: string;
  contact_type: ContactType;
  coaching_type?: CoachingType;
  tags?: string[];
  source?: string;
}

export interface OrganizationFormData {
  name: string;
  industry?: string;
  size?: string;
  website?: string;
  segment?: string;
  source?: string;
  tags?: string[];
}

export interface InteractionFormData {
  contact_id: string;
  interaction_type: InteractionType;
  subject?: string;
  content?: string;
  direction?: Direction;
}

// Booking types
export interface BookingType {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  duration_minutes: number;
  color: string;
  price: number | null;
  buffer_before: number;
  buffer_after: number;
  min_notice_hours: number;
  max_advance_days: number;
  max_per_day: number | null;
  requires_confirmation: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BookingTypeFormData {
  name: string;
  slug: string;
  description?: string;
  duration_minutes: number;
  color: string;
  price?: number;
  buffer_before?: number;
  buffer_after?: number;
  min_notice_hours?: number;
  max_advance_days?: number;
  max_per_day?: number;
  requires_confirmation?: boolean;
  is_active?: boolean;
}

// Availability types
export interface Availability {
  id: string;
  user_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
  created_at: string;
}

export interface WeeklyAvailability {
  monday: Availability[];
  tuesday: Availability[];
  wednesday: Availability[];
  thursday: Availability[];
  friday: Availability[];
  saturday: Availability[];
  sunday: Availability[];
}

export interface AvailabilityOverride {
  id: string;
  user_id: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  is_available: boolean;
  reason: string | null;
  created_at: string;
}

// Booking types
export type BookingStatus = "pending" | "confirmed" | "completed" | "cancelled" | "no_show";

export interface Booking {
  id: string;
  booking_type_id: string;
  contact_id: string;
  start_time: string;
  end_time: string;
  status: BookingStatus;
  google_event_id: string | null;
  notes: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;
  cancelled_by: string | null;
  confirmation_token: string;
  reminder_sent_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingWithDetails extends Booking {
  booking_type: BookingType;
  contact: Contact;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

export interface PublicBookingTypeInfo {
  name: string;
  slug: string;
  description: string | null;
  duration_minutes: number;
  price: number | null;
  min_notice_hours: number;
  max_advance_days: number;
}
