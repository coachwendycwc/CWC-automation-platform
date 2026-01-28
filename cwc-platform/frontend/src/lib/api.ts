const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ApiOptions extends RequestInit {
  token?: string;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new ApiError(response.status, error.detail || "An error occurred");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    fetchApi<{ access_token: string; user: any }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, name: string) =>
    fetchApi<{ access_token: string; user: any }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  forgotPassword: (email: string) =>
    fetchApi<{ message: string }>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, password: string) =>
    fetchApi<{ message: string }>("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),

  getMe: (token: string) =>
    fetchApi<any>("/api/auth/me", { token }),

  devLogin: (email?: string) =>
    fetchApi<{ access_token: string; user: any }>("/api/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  googleAuth: (accessToken: string) =>
    fetchApi<{ access_token: string; user: any }>("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ access_token: accessToken }),
    }),
};

// Organizations API
export const organizationsApi = {
  list: (token: string, params?: { page?: number; size?: number; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.size) searchParams.set("size", params.size.toString());
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any>(`/api/organizations?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/organizations/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/organizations", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/organizations/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/organizations/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Contacts API
export const contactsApi = {
  list: (token: string, params?: { page?: number; size?: number; search?: string; contact_type?: string; organization_id?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.size) searchParams.set("size", params.size.toString());
    if (params?.search) searchParams.set("search", params.search);
    if (params?.contact_type) searchParams.set("contact_type", params.contact_type);
    if (params?.organization_id) searchParams.set("organization_id", params.organization_id);
    return fetchApi<any>(`/api/contacts?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/contacts/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/contacts", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/contacts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/contacts/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Interactions API
export const interactionsApi = {
  listForContact: (token: string, contactId: string) =>
    fetchApi<any>(`/api/interactions/contact/${contactId}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/interactions", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/interactions/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Booking Types API
export const bookingTypesApi = {
  list: (token: string, activeOnly?: boolean) => {
    const params = activeOnly ? "?active_only=true" : "";
    return fetchApi<any>(`/api/booking-types${params}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/booking-types/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/booking-types", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/booking-types/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/booking-types/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Availability API
export const availabilityApi = {
  getWeekly: (token: string) =>
    fetchApi<any>("/api/availability", { token }),

  updateWeekly: (token: string, data: { availabilities: any[] }) =>
    fetchApi<any>("/api/availability", {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  listOverrides: (token: string) =>
    fetchApi<any>("/api/availability/overrides", { token }),

  createOverride: (token: string, data: any) =>
    fetchApi<any>("/api/availability/overrides", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  deleteOverride: (token: string, id: string) =>
    fetchApi<void>(`/api/availability/overrides/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Bookings API
export const bookingsApi = {
  list: (token: string, params?: { status?: string; booking_type_id?: string; start_date?: string; end_date?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.booking_type_id) searchParams.set("booking_type_id", params.booking_type_id);
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());
    return fetchApi<any>(`/api/bookings?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/bookings/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/bookings", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/bookings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  confirm: (token: string, id: string) =>
    fetchApi<any>(`/api/bookings/${id}/confirm`, {
      method: "POST",
      token,
    }),

  cancel: (token: string, id: string, reason?: string) =>
    fetchApi<any>(`/api/bookings/${id}/cancel?reason=${encodeURIComponent(reason || "")}`, {
      method: "POST",
      token,
    }),
};

// Public Booking API (no auth required)
export const publicBookingApi = {
  getBookingType: (slug: string) =>
    fetchApi<any>(`/api/book/${slug}`),

  getSlots: (slug: string, date: string) =>
    fetchApi<any>(`/api/book/${slug}/slots?date=${date}`),

  createBooking: (slug: string, data: any) =>
    fetchApi<any>(`/api/book/${slug}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getBookingByToken: (token: string) =>
    fetchApi<any>(`/api/book/manage/${token}`),

  rescheduleBooking: (token: string, newStartTime: string) =>
    fetchApi<any>(`/api/book/manage/${token}/reschedule`, {
      method: "POST",
      body: JSON.stringify({ new_start_time: newStartTime }),
    }),

  cancelBooking: (token: string, reason?: string) =>
    fetchApi<any>(`/api/book/manage/${token}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
};

// Invoices API
export const invoicesApi = {
  list: (token: string, params?: { status?: string; contact_id?: string; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/invoices?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/invoices/${id}`, { token }),

  getStats: (token: string) =>
    fetchApi<any>("/api/invoices/stats", { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/invoices", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/invoices/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/invoices/${id}`, {
      method: "DELETE",
      token,
    }),

  send: (token: string, id: string, data?: { send_email?: boolean; email_message?: string }) =>
    fetchApi<any>(`/api/invoices/${id}/send`, {
      method: "POST",
      body: JSON.stringify(data || { send_email: true }),
      token,
    }),

  duplicate: (token: string, id: string) =>
    fetchApi<any>(`/api/invoices/${id}/duplicate`, {
      method: "POST",
      token,
    }),

  cancel: (token: string, id: string) =>
    fetchApi<any>(`/api/invoices/${id}/cancel`, {
      method: "POST",
      token,
    }),
};

// Payments API
export const paymentsApi = {
  listForInvoice: (token: string, invoiceId: string) =>
    fetchApi<any[]>(`/api/invoices/${invoiceId}/payments`, { token }),

  record: (token: string, invoiceId: string, data: any) =>
    fetchApi<any>(`/api/invoices/${invoiceId}/payments`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, paymentId: string) =>
    fetchApi<void>(`/api/payments/${paymentId}`, {
      method: "DELETE",
      token,
    }),
};

// Payment Plans API
export const paymentPlansApi = {
  get: (token: string, invoiceId: string) =>
    fetchApi<any>(`/api/invoices/${invoiceId}/payment-plan`, { token }),

  create: (token: string, invoiceId: string, data: any) =>
    fetchApi<any>(`/api/invoices/${invoiceId}/payment-plan`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  cancel: (token: string, planId: string) =>
    fetchApi<void>(`/api/payment-plans/${planId}`, {
      method: "DELETE",
      token,
    }),
};

// Public Invoice API (no auth required)
export const publicInvoiceApi = {
  get: (viewToken: string) =>
    fetchApi<any>(`/api/invoice/${viewToken}`),

  pay: (viewToken: string) =>
    fetchApi<any>(`/api/invoice/${viewToken}/pay`, {
      method: "POST",
    }),
};

// Stripe API
export const stripeApi = {
  getConfig: () =>
    fetchApi<{ public_key: string; is_configured: boolean }>("/api/stripe/config"),

  createCheckoutByToken: (viewToken: string) =>
    fetchApi<{ url: string; session_id: string }>("/api/stripe/checkout", {
      method: "POST",
      body: JSON.stringify({ view_token: viewToken }),
    }),

  createCheckoutById: (invoiceId: string) =>
    fetchApi<{ url: string; session_id: string }>("/api/stripe/checkout", {
      method: "POST",
      body: JSON.stringify({ invoice_id: invoiceId }),
    }),
};

// Contract Templates API
export const contractTemplatesApi = {
  list: (token: string, params?: { category?: string; is_active?: boolean; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    if (params?.is_active !== undefined) searchParams.set("is_active", params.is_active.toString());
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/contract-templates?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/contract-templates/${id}`, { token }),

  preview: (token: string, id: string) =>
    fetchApi<any>(`/api/contract-templates/${id}/preview`, { token }),

  getMergeFields: (token: string) =>
    fetchApi<any>("/api/contract-templates/merge-fields", { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/contract-templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/contract-templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/contract-templates/${id}`, {
      method: "DELETE",
      token,
    }),

  duplicate: (token: string, id: string) =>
    fetchApi<any>(`/api/contract-templates/${id}/duplicate`, {
      method: "POST",
      token,
    }),
};

// Contracts API
export const contractsApi = {
  list: (token: string, params?: { status?: string; contact_id?: string; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/contracts?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/contracts/${id}`, { token }),

  getStats: (token: string) =>
    fetchApi<any>("/api/contracts/stats", { token }),

  getAuditLog: (token: string, id: string) =>
    fetchApi<any[]>(`/api/contracts/${id}/audit-log`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/contracts", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/contracts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/contracts/${id}`, {
      method: "DELETE",
      token,
    }),

  send: (token: string, id: string, data?: { send_email?: boolean; email_message?: string; expiry_days?: number }) =>
    fetchApi<any>(`/api/contracts/${id}/send`, {
      method: "POST",
      body: JSON.stringify(data || { send_email: true }),
      token,
    }),

  resend: (token: string, id: string, data?: { send_email?: boolean; email_message?: string; expiry_days?: number }) =>
    fetchApi<any>(`/api/contracts/${id}/resend`, {
      method: "POST",
      body: JSON.stringify(data || { send_email: true }),
      token,
    }),

  duplicate: (token: string, id: string) =>
    fetchApi<any>(`/api/contracts/${id}/duplicate`, {
      method: "POST",
      token,
    }),

  void: (token: string, id: string, reason?: string) =>
    fetchApi<any>(`/api/contracts/${id}/void`, {
      method: "POST",
      body: JSON.stringify({ reason }),
      token,
    }),

  downloadPdf: (token: string, id: string) =>
    // Return the URL for PDF download (handled differently)
    `${API_URL}/api/contracts/${id}/pdf`,
};

// Public Contract API (no auth required)
export const publicContractApi = {
  get: (viewToken: string) =>
    fetchApi<any>(`/api/contract/${viewToken}`),

  getStatus: (viewToken: string) =>
    fetchApi<any>(`/api/contract/${viewToken}/status`),

  sign: (viewToken: string, data: {
    signer_name: string;
    signer_email: string;
    signature_data: string;
    signature_type: "drawn" | "typed";
    agreed_to_terms: boolean;
  }) =>
    fetchApi<any>(`/api/contract/${viewToken}/sign`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  decline: (viewToken: string, reason?: string) =>
    fetchApi<any>(`/api/contract/${viewToken}/decline`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
};

// Project Templates API
export const projectTemplatesApi = {
  list: (token: string, params?: { project_type?: string; active_only?: boolean; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_type) searchParams.set("project_type", params.project_type);
    if (params?.active_only !== undefined) searchParams.set("active_only", params.active_only.toString());
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/project-templates?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/project-templates/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/project-templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/project-templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/project-templates/${id}`, {
      method: "DELETE",
      token,
    }),

  duplicate: (token: string, id: string) =>
    fetchApi<any>(`/api/project-templates/${id}/duplicate`, {
      method: "POST",
      token,
    }),
};

// Projects API
export const projectsApi = {
  list: (token: string, params?: { status?: string; project_type?: string; contact_id?: string; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.project_type) searchParams.set("project_type", params.project_type);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/projects?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/projects/${id}`, { token }),

  getStats: (token: string) =>
    fetchApi<any>("/api/projects/stats", { token }),

  getActivity: (token: string, id: string) =>
    fetchApi<any[]>(`/api/projects/${id}/activity`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/projects/${id}`, {
      method: "DELETE",
      token,
    }),

  complete: (token: string, id: string) =>
    fetchApi<any>(`/api/projects/${id}/complete`, {
      method: "POST",
      token,
    }),

  duplicate: (token: string, id: string, data?: { new_title?: string; include_tasks?: boolean }) =>
    fetchApi<any>(`/api/projects/${id}/duplicate`, {
      method: "POST",
      body: JSON.stringify(data || {}),
      token,
    }),
};

// Tasks API
export const tasksApi = {
  listForProject: (token: string, projectId: string, params?: { status?: string; priority?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.priority) searchParams.set("priority", params.priority);
    return fetchApi<any[]>(`/api/projects/${projectId}/tasks?${searchParams}`, { token });
  },

  listAll: (token: string, params?: { status?: string; priority?: string; assigned_to?: string; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.priority) searchParams.set("priority", params.priority);
    if (params?.assigned_to) searchParams.set("assigned_to", params.assigned_to);
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<any[]>(`/api/tasks?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/tasks/${id}`, { token }),

  getStats: (token: string, projectId?: string) => {
    const params = projectId ? `?project_id=${projectId}` : "";
    return fetchApi<any>(`/api/tasks/stats${params}`, { token });
  },

  create: (token: string, projectId: string, data: any) =>
    fetchApi<any>(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ ...data, project_id: projectId }),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/tasks/${id}`, {
      method: "DELETE",
      token,
    }),

  complete: (token: string, id: string) =>
    fetchApi<any>(`/api/tasks/${id}/complete`, {
      method: "POST",
      token,
    }),

  reorder: (token: string, updates: Array<{ id: string; status?: string; order_index: number }>) =>
    fetchApi<any>("/api/tasks/reorder", {
      method: "PUT",
      body: JSON.stringify({ task_updates: updates }),
      token,
    }),
};

// Time Entries API
export const timeEntriesApi = {
  listForTask: (token: string, taskId: string) =>
    fetchApi<any[]>(`/api/tasks/${taskId}/time-entries`, { token }),

  create: (token: string, taskId: string, data: any) =>
    fetchApi<any>(`/api/tasks/${taskId}/time-entries`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, entryId: string) =>
    fetchApi<void>(`/api/time-entries/${entryId}`, {
      method: "DELETE",
      token,
    }),
};

// Extractions API (AI Invoice Extraction)
export const extractionsApi = {
  getStats: (token: string) =>
    fetchApi<{
      pending_webhooks: number;
      pending_extractions: number;
      approved_today: number;
      total_extracted_value: number;
    }>("/api/extractions/stats", { token }),

  listWebhooks: (token: string, status?: string) => {
    const params = status ? `?status_filter=${status}` : "";
    return fetchApi<any[]>(`/api/extractions/webhooks${params}`, { token });
  },

  list: (token: string, params?: { status?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status_filter", params.status);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());
    return fetchApi<{
      items: any[];
      total: number;
      pending_count: number;
      approved_count: number;
    }>(`/api/extractions?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/extractions/${id}`, { token }),

  process: (token: string, webhookId: string) =>
    fetchApi<any>(`/api/extractions/process/${webhookId}`, {
      method: "POST",
      token,
    }),

  review: (token: string, id: string, data: {
    action: "approve" | "reject" | "edit";
    corrections?: Array<{ field: string; original: any; corrected: any }>;
    notes?: string;
  }) =>
    fetchApi<any>(`/api/extractions/${id}/review`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  createInvoice: (token: string, id: string) =>
    fetchApi<{ invoice_id: string }>(`/api/extractions/${id}/create-invoice`, {
      method: "POST",
      token,
    }),
};

// Reports API
export const reportsApi = {
  getDashboard: (token: string) =>
    fetchApi<{
      revenue: { total: number; this_month: number; outstanding: number };
      invoices: { draft: number; sent: number; partial: number; paid: number; overdue: number };
      contacts: number;
      projects: { active: number };
      bookings: { this_month: number; upcoming: number };
    }>("/api/reports/dashboard", { token }),

  getMonthlyRevenue: (token: string, year?: number) => {
    const params = year ? `?year=${year}` : "";
    return fetchApi<{
      year: number;
      months: Array<{ month: string; month_num: number; revenue: number }>;
      total: number;
    }>(`/api/reports/revenue/monthly${params}`, { token });
  },

  getInvoiceAging: (token: string) =>
    fetchApi<{
      current: { invoices: any[]; total: number; count: number };
      "1_30_days": { invoices: any[]; total: number; count: number };
      "31_60_days": { invoices: any[]; total: number; count: number };
      "61_90_days": { invoices: any[]; total: number; count: number };
      "90_plus_days": { invoices: any[]; total: number; count: number };
      summary: { total_outstanding: number; total_invoices: number };
    }>("/api/reports/invoices/aging", { token }),

  getProjectHours: (token: string, projectId?: string) => {
    const params = projectId ? `?project_id=${projectId}` : "";
    return fetchApi<{
      projects: Array<{
        id: string;
        project_number: string;
        title: string;
        status: string;
        logged_hours: number;
        estimated_hours: number;
        remaining_hours: number | null;
        percent_used: number | null;
      }>;
      summary: { total_logged_hours: number; total_estimated_hours: number; total_remaining: number };
    }>(`/api/reports/projects/hours${params}`, { token });
  },

  getContactEngagement: (token: string, limit?: number) => {
    const params = limit ? `?limit=${limit}` : "";
    return fetchApi<{
      top_contacts: Array<{
        id: string;
        name: string;
        email: string;
        total_revenue: number;
        invoice_count: number;
      }>;
      activity: { active_last_30_days: number; total_contacts: number; engagement_rate: number };
    }>(`/api/reports/contacts/engagement${params}`, { token });
  },

  exportInvoicesCsv: (token: string) =>
    `${API_URL}/api/reports/export/invoices`,

  exportPaymentsCsv: (token: string) =>
    `${API_URL}/api/reports/export/payments`,

  exportTimeEntriesCsv: (token: string, projectId?: string) => {
    const params = projectId ? `?project_id=${projectId}` : "";
    return `${API_URL}/api/reports/export/time-entries${params}`;
  },

  // Profit & Loss
  getProfitLoss: (token: string, params?: { tax_year?: number; start_date?: string; end_date?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.tax_year) searchParams.set("tax_year", params.tax_year.toString());
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    return fetchApi<{
      period_start: string;
      period_end: string;
      total_revenue: number;
      invoices_paid: number;
      total_expenses: number;
      expenses_by_category: Array<{ category: string; amount: number; count: number }>;
      total_mileage_deduction: number;
      total_contractor_payments: number;
      net_profit: number;
      profit_margin: number | null;
    }>(`/api/reports/profit-loss?${searchParams}`, { token });
  },

  // Tax Summary
  getTaxSummary: (token: string, taxYear: number) =>
    fetchApi<{
      tax_year: number;
      gross_income: number;
      total_expenses: number;
      mileage_deduction: number;
      contractor_payments: number;
      total_deductions: number;
      estimated_taxable_income: number;
      quarters: Array<{ quarter: number; income: number; expenses: number; mileage: number; net: number }>;
      contractors_needing_1099: Array<{
        contractor_id: string;
        contractor_name: string;
        total_paid: number;
        payment_count: number;
        needs_1099: boolean;
      }>;
    }>(`/api/reports/tax-summary/${taxYear}`, { token }),

  // Export functions
  exportExpensesCsv: (taxYear?: number) => {
    const params = taxYear ? `?tax_year=${taxYear}` : "";
    return `${API_URL}/api/reports/export/expenses${params}`;
  },

  exportMileageCsv: (taxYear?: number) => {
    const params = taxYear ? `?tax_year=${taxYear}` : "";
    return `${API_URL}/api/reports/export/mileage${params}`;
  },

  exportContractorsCsv: (taxYear?: number) => {
    const params = taxYear ? `?tax_year=${taxYear}` : "";
    return `${API_URL}/api/reports/export/contractors${params}`;
  },
};

// Expense Categories API
export const expenseCategoriesApi = {
  list: (token: string, includeInactive?: boolean) => {
    const params = includeInactive ? "?include_inactive=true" : "";
    return fetchApi<any[]>(`/api/expenses/categories${params}`, { token });
  },

  create: (token: string, data: any) =>
    fetchApi<any>("/api/expenses/categories", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/expenses/categories/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/expenses/categories/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Expenses API
export const expensesApi = {
  list: (token: string, params?: {
    page?: number;
    size?: number;
    category_id?: string;
    vendor?: string;
    start_date?: string;
    end_date?: string;
    tax_year?: number;
    is_recurring?: boolean;
    search?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.size) searchParams.set("size", params.size.toString());
    if (params?.category_id) searchParams.set("category_id", params.category_id);
    if (params?.vendor) searchParams.set("vendor", params.vendor);
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    if (params?.tax_year) searchParams.set("tax_year", params.tax_year.toString());
    if (params?.is_recurring !== undefined) searchParams.set("is_recurring", params.is_recurring.toString());
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<{ items: any[]; total: number; page: number; size: number }>(`/api/expenses?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/expenses/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/expenses", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/expenses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/expenses/${id}`, {
      method: "DELETE",
      token,
    }),

  getSummary: (token: string, taxYear: number) =>
    fetchApi<{
      total_expenses: number;
      total_deductible: number;
      by_category: Array<{ category: string; amount: number; count: number }>;
      by_month: Array<{ month: number; amount: number }>;
    }>(`/api/expenses/summary/${taxYear}`, { token }),
};

// Recurring Expenses API
export const recurringExpensesApi = {
  list: (token: string, isActive?: boolean) => {
    const params = isActive !== undefined ? `?is_active=${isActive}` : "";
    return fetchApi<any[]>(`/api/expenses/recurring${params}`, { token });
  },

  create: (token: string, data: any) =>
    fetchApi<any>("/api/expenses/recurring", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/expenses/recurring/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/expenses/recurring/${id}`, {
      method: "DELETE",
      token,
    }),

  generate: (token: string, id: string, expenseDate?: string) => {
    const params = expenseDate ? `?expense_date=${expenseDate}` : "";
    return fetchApi<any>(`/api/expenses/recurring/${id}/generate${params}`, {
      method: "POST",
      token,
    });
  },
};

// Mileage API
export const mileageApi = {
  list: (token: string, params?: {
    tax_year?: number;
    purpose?: string;
    contact_id?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.tax_year) searchParams.set("tax_year", params.tax_year.toString());
    if (params?.purpose) searchParams.set("purpose", params.purpose);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    return fetchApi<{ items: any[]; total: number }>(`/api/mileage?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/mileage/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/mileage", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/mileage/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/mileage/${id}`, {
      method: "DELETE",
      token,
    }),

  getSummary: (token: string, taxYear: number) =>
    fetchApi<{
      total_miles: number;
      total_deduction: number;
      trip_count: number;
      by_purpose: Array<{ purpose: string; miles: number; amount: number }>;
    }>(`/api/mileage/summary/${taxYear}`, { token }),

  getRates: (token: string) =>
    fetchApi<Array<{ year: number; rate_per_mile: number; source: string }>>("/api/mileage/rates", { token }),
};

// Contractors API
export const contractorsApi = {
  list: (token: string, params?: { is_active?: boolean; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.is_active !== undefined) searchParams.set("is_active", params.is_active.toString());
    if (params?.search) searchParams.set("search", params.search);
    return fetchApi<{ items: any[]; total: number }>(`/api/contractors?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/contractors/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/contractors", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/contractors/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/contractors/${id}`, {
      method: "DELETE",
      token,
    }),

  // Payments
  listPayments: (token: string, contractorId: string, taxYear?: number) => {
    const params = taxYear ? `?tax_year=${taxYear}` : "";
    return fetchApi<any[]>(`/api/contractors/${contractorId}/payments${params}`, { token });
  },

  createPayment: (token: string, data: any) =>
    fetchApi<any>("/api/contractors/payments", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updatePayment: (token: string, paymentId: string, data: any) =>
    fetchApi<any>(`/api/contractors/payments/${paymentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deletePayment: (token: string, paymentId: string) =>
    fetchApi<void>(`/api/contractors/payments/${paymentId}`, {
      method: "DELETE",
      token,
    }),

  // 1099 Summary
  get1099Summary: (token: string, taxYear: number) =>
    fetchApi<Array<{
      contractor_id: string;
      contractor_name: string;
      total_paid: number;
      payment_count: number;
      needs_1099: boolean;
    }>>(`/api/contractors/1099/${taxYear}`, { token }),
};

// Offboarding API
export const offboardingApi = {
  list: (token: string, params?: { page?: number; size?: number; status?: string; workflow_type?: string; contact_id?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.size) searchParams.set("size", params.size.toString());
    if (params?.status) searchParams.set("status", params.status);
    if (params?.workflow_type) searchParams.set("workflow_type", params.workflow_type);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    return fetchApi<{ items: any[]; total: number }>(`/api/offboarding?${searchParams}`, { token });
  },

  getStats: (token: string) =>
    fetchApi<{
      total_workflows: number;
      pending: number;
      in_progress: number;
      completed: number;
      cancelled: number;
      surveys_sent: number;
      surveys_completed: number;
      testimonials_received: number;
      testimonials_approved: number;
      avg_satisfaction: number | null;
      avg_nps: number | null;
    }>("/api/offboarding/stats", { token }),

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/offboarding/${id}`, { token }),

  initiate: (token: string, data: {
    contact_id: string;
    workflow_type: "client" | "project" | "contract";
    related_project_id?: string;
    related_contract_id?: string;
    template_id?: string;
    send_survey?: boolean;
    request_testimonial?: boolean;
    send_certificate?: boolean;
    notes?: string;
  }) =>
    fetchApi<any>("/api/offboarding/initiate", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/offboarding/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  toggleChecklistItem: (token: string, id: string, itemIndex: number) =>
    fetchApi<any>(`/api/offboarding/${id}/checklist/${itemIndex}`, {
      method: "POST",
      token,
    }),

  complete: (token: string, id: string) =>
    fetchApi<any>(`/api/offboarding/${id}/complete`, {
      method: "POST",
      token,
    }),

  cancel: (token: string, id: string, reason?: string) =>
    fetchApi<any>(`/api/offboarding/${id}/cancel?${reason ? `reason=${encodeURIComponent(reason)}` : ""}`, {
      method: "POST",
      token,
    }),

  getActivity: (token: string, id: string) =>
    fetchApi<any[]>(`/api/offboarding/${id}/activity`, { token }),

  sendCompletionEmail: (token: string, id: string, customMessage?: string) =>
    fetchApi<{ success: boolean }>(`/api/offboarding/${id}/send-completion-email`, {
      method: "POST",
      body: JSON.stringify({ custom_message: customMessage }),
      token,
    }),

  sendSurvey: (token: string, id: string) =>
    fetchApi<{ success: boolean }>(`/api/offboarding/${id}/send-survey`, {
      method: "POST",
      token,
    }),

  requestTestimonial: (token: string, id: string) =>
    fetchApi<{ success: boolean }>(`/api/offboarding/${id}/request-testimonial`, {
      method: "POST",
      token,
    }),

  approveTestimonial: (token: string, id: string) =>
    fetchApi<any>(`/api/offboarding/${id}/approve-testimonial`, {
      method: "POST",
      token,
    }),
};

// Offboarding Templates API
export const offboardingTemplatesApi = {
  list: (token: string, params?: { workflow_type?: string; active_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.workflow_type) searchParams.set("workflow_type", params.workflow_type);
    if (params?.active_only !== undefined) searchParams.set("active_only", params.active_only.toString());
    return fetchApi<any[]>(`/api/offboarding-templates?${searchParams}`, { token });
  },

  get: (token: string, id: string) =>
    fetchApi<any>(`/api/offboarding-templates/${id}`, { token }),

  create: (token: string, data: any) =>
    fetchApi<any>("/api/offboarding-templates", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: any) =>
    fetchApi<any>(`/api/offboarding-templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/offboarding-templates/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Public Feedback API (no auth required)
export const publicFeedbackApi = {
  getSurvey: (token: string) =>
    fetchApi<{
      contact_name: string;
      workflow_type: string;
      project_title: string | null;
      already_completed: boolean;
    }>(`/api/feedback/${token}`),

  submitSurvey: (token: string, response: {
    // Section 1: Overall Experience (required)
    satisfaction_rating: number;
    nps_score: number;
    initial_goals?: string;
    // Section 2: Growth + Measurement
    outcomes?: string[];
    outcomes_other?: string;
    specific_wins?: string;
    progress_rating?: number;
    most_transformative?: string;
    // Section 3: Coaching Process
    helpful_parts?: string[];
    helpful_parts_other?: string;
    least_helpful?: string;
    wish_done_earlier?: string;
    // Section 4: Equity, Safety, Support
    psychological_safety?: string;
    woc_support_rating?: number;
    support_feedback?: string;
    // Section 5: Testimonial
    may_share_testimonial?: string;
    display_name_title?: string;
    written_testimonial?: string;
    willing_to_record_video?: boolean;
    video_upload_preference?: string;
    video_url?: string;
    video_public_id?: string;
    video_duration_seconds?: number;
    video_thumbnail_url?: string | null;
    // Legacy/Final
    most_valued?: string;
    improvement_suggestions?: string;
    additional_comments?: string;
  }) =>
    fetchApi<{ success: boolean; message: string }>(`/api/feedback/${token}`, {
      method: "POST",
      body: JSON.stringify(response),
    }),

  getTestimonialRequest: (token: string) =>
    fetchApi<{
      contact_name: string;
      workflow_type: string;
      already_submitted: boolean;
    }>(`/api/testimonial/${token}`),

  submitTestimonial: (token: string, submission: {
    testimonial_text: string;
    author_name: string;
    author_title?: string | null;
    photo?: string | null;
    permission_granted: boolean;
  }) =>
    fetchApi<{ success: boolean; message: string }>(`/api/testimonial/${token}`, {
      method: "POST",
      body: JSON.stringify(submission),
    }),
};

// Client Portal Auth API
export const clientAuthApi = {
  requestLogin: (email: string) =>
    fetchApi<{ message: string }>("/api/client/auth/request-login", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  verifyToken: (token: string) =>
    fetchApi<{
      session_token: string;
      contact: {
        id: string;
        first_name: string;
        last_name: string | null;
        email: string | null;
        organization_id: string | null;
        organization_name: string | null;
        organization_logo_url: string | null;
        is_org_admin: boolean;
      };
    }>("/api/client/auth/verify-token", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  getMe: (sessionToken: string) =>
    fetchApi<{
      id: string;
      first_name: string;
      last_name: string | null;
      email: string | null;
      organization_id: string | null;
      organization_name: string | null;
      organization_logo_url: string | null;
      is_org_admin: boolean;
    }>("/api/client/auth/me", {
      token: sessionToken,
    }),

  logout: (sessionToken: string) =>
    fetchApi<{ message: string }>("/api/client/auth/logout", {
      method: "POST",
      token: sessionToken,
    }),
};

// Client Portal Data API
export const clientPortalApi = {
  getDashboard: (sessionToken: string) =>
    fetchApi<{
      stats: {
        unpaid_invoices: number;
        total_due: number;
        upcoming_bookings: number;
        active_projects: number;
        pending_contracts: number;
      };
      recent_invoices: any[];
      upcoming_bookings: any[];
    }>(`/api/client/dashboard`, {
      token: sessionToken,
    }),

  // Invoices (for independent coachees only)
  getInvoices: (sessionToken: string, status?: string) => {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    return fetchApi<any[]>(`/api/client/invoices?${params}`, {
      token: sessionToken,
    });
  },

  getInvoice: (sessionToken: string, id: string) =>
    fetchApi<any>(`/api/client/invoices/${id}`, {
      token: sessionToken,
    }),

  // Contracts (for independent coachees only)
  getContracts: (sessionToken: string, status?: string) => {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    return fetchApi<any[]>(`/api/client/contracts?${params}`, {
      token: sessionToken,
    });
  },

  getContract: (sessionToken: string, id: string) =>
    fetchApi<any>(`/api/client/contracts/${id}`, {
      token: sessionToken,
    }),

  downloadContractPdf: async (sessionToken: string, id: string) => {
    const response = await fetch(`${API_URL}/api/client/contracts/${id}/pdf`, {
      headers: {
        Authorization: `Bearer ${sessionToken}`,
      },
    });
    if (!response.ok) {
      throw new Error("Failed to download PDF");
    }
    return response.blob();
  },

  // Bookings
  listBookings: (sessionToken: string, upcomingOnly?: boolean) => {
    const params = upcomingOnly ? "?upcoming_only=true" : "";
    return fetchApi<any[]>(`/api/client/bookings${params}`, {
      token: sessionToken,
    });
  },

  getBooking: (sessionToken: string, id: string) =>
    fetchApi<any>(`/api/client/bookings/${id}`, {
      token: sessionToken,
    }),

  cancelBooking: (sessionToken: string, id: string) =>
    fetchApi<{ message: string }>(`/api/client/bookings/${id}/cancel`, {
      method: "POST",
      token: sessionToken,
    }),

  // Projects
  getProjects: (sessionToken: string) =>
    fetchApi<any[]>(`/api/client/projects`, {
      token: sessionToken,
    }),

  getProject: (sessionToken: string, id: string) =>
    fetchApi<any>(`/api/client/projects/${id}`, {
      token: sessionToken,
    }),

  // Profile
  getProfile: (sessionToken: string) =>
    fetchApi<{
      id: string;
      first_name: string;
      last_name: string | null;
      email: string | null;
      phone: string | null;
      organization_name: string | null;
      is_org_admin: boolean;
    }>("/api/client/profile", {
      token: sessionToken,
    }),

  updateProfile: (sessionToken: string, data: {
    first_name?: string;
    last_name?: string;
    phone?: string;
  }) =>
    fetchApi<any>("/api/client/profile", {
      method: "PUT",
      body: JSON.stringify(data),
      token: sessionToken,
    }),

  // Sessions / Recordings (always personal - content is private)
  getSessions: (sessionToken: string) =>
    fetchApi<any[]>(`/api/client/sessions`, {
      token: sessionToken,
    }),

  getSession: (sessionToken: string, id: string) =>
    fetchApi<{
      id: string;
      meeting_title: string | null;
      recorded_at: string | null;
      duration_seconds: number | null;
      recording_url: string | null;
      transcript: string | null;
      summary: any;
      action_items: string[] | null;
      homework: Array<{ description: string; completed: boolean }> | null;
    }>(`/api/client/sessions/${id}`, {
      token: sessionToken,
    }),

  updateHomeworkStatus: (sessionToken: string, sessionId: string, homeworkIndex: number, completed: boolean) =>
    fetchApi<{ message: string }>(`/api/client/sessions/${sessionId}/homework/${homeworkIndex}?completed=${completed}`, {
      method: "PUT",
      token: sessionToken,
    }),

  // Organization (for org admins)
  getOrganizationDashboard: (sessionToken: string) =>
    fetchApi<{
      organization_name: string;
      organization_id: string;
      billing: {
        total_invoiced: number;
        total_paid: number;
        total_outstanding: number;
        invoice_count: number;
      };
      usage: {
        total_employees: number;
        employees_with_sessions: number;
        total_sessions_completed: number;
        total_sessions_upcoming: number;
        total_coaching_hours: number;
      };
      recent_invoices: any[];
      pending_contracts: number;
    }>("/api/client/organization", {
      token: sessionToken,
    }),

  getOrganizationEmployees: (sessionToken: string) =>
    fetchApi<Array<{
      id: string;
      first_name: string;
      last_name: string | null;
      email: string | null;
      sessions_completed: number;
      sessions_upcoming: number;
      last_session_date: string | null;
    }>>("/api/client/organization/employees", {
      token: sessionToken,
    }),

  // Resources / Content
  getResources: (sessionToken: string, category?: string) => {
    const params = category ? `?category=${encodeURIComponent(category)}` : "";
    return fetchApi<Array<{
      id: string;
      title: string;
      description: string | null;
      content_type: string;
      category: string | null;
      file_name: string | null;
      file_size: number | null;
      external_url: string | null;
      release_date: string | null;
      is_released: boolean;
      created_at: string;
    }>>(`/api/client/resources${params}`, {
      token: sessionToken,
    });
  },

  getResource: (sessionToken: string, id: string) =>
    fetchApi<{
      id: string;
      title: string;
      description: string | null;
      content_type: string;
      category: string | null;
      file_name: string | null;
      file_size: number | null;
      file_url: string | null;
      external_url: string | null;
      mime_type: string | null;
      release_date: string | null;
      is_released: boolean;
      created_at: string;
    }>(`/api/client/resources/${id}`, {
      token: sessionToken,
    }),

  getResourceCategories: (sessionToken: string) =>
    fetchApi<{ categories: string[] }>("/api/client/resources/categories/list", {
      token: sessionToken,
    }),

  // Notes
  getNotes: (sessionToken: string) =>
    fetchApi<Array<{
      id: string;
      content: string;
      direction: "to_coach" | "to_client";
      is_read: boolean;
      created_at: string;
    }>>("/api/client/notes", {
      token: sessionToken,
    }),

  createNote: (sessionToken: string, content: string) =>
    fetchApi<{
      id: string;
      content: string;
      direction: "to_coach" | "to_client";
      is_read: boolean;
      created_at: string;
    }>("/api/client/notes", {
      method: "POST",
      body: JSON.stringify({ content }),
      token: sessionToken,
    }),

  markNoteRead: (sessionToken: string, noteId: string) =>
    fetchApi<{
      id: string;
      content: string;
      direction: "to_coach" | "to_client";
      is_read: boolean;
      created_at: string;
    }>(`/api/client/notes/${noteId}/read`, {
      method: "PUT",
      token: sessionToken,
    }),

  getUnreadNotesCount: (sessionToken: string) =>
    fetchApi<{ count: number }>("/api/client/notes/unread-count", {
      token: sessionToken,
    }),

  // Action Items
  getActionItems: (sessionToken: string, status?: string) => {
    const params = status ? `?status=${status}` : "";
    return fetchApi<Array<{
      id: string;
      title: string;
      description: string | null;
      due_date: string | null;
      priority: string;
      status: string;
      completed_at: string | null;
      created_at: string;
    }>>(`/api/client/action-items${params}`, {
      token: sessionToken,
    });
  },

  updateActionItemStatus: (
    sessionToken: string,
    itemId: string,
    status: "completed" | "skipped" | "in_progress"
  ) =>
    fetchApi<{
      id: string;
      title: string;
      description: string | null;
      due_date: string | null;
      priority: string;
      status: string;
      completed_at: string | null;
      created_at: string;
    }>(`/api/client/action-items/${itemId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
      token: sessionToken,
    }),

  getPendingActionItemsCount: (sessionToken: string) =>
    fetchApi<{ count: number }>("/api/client/action-items/pending-count", {
      token: sessionToken,
    }),

  // Goals
  getGoals: (sessionToken: string, status?: string) => {
    const params = status ? `?status=${status}` : "";
    return fetchApi<Array<{
      id: string;
      title: string;
      description: string | null;
      category: string | null;
      status: string;
      target_date: string | null;
      progress_percent: number;
      milestones: Array<{
        id: string;
        goal_id: string;
        title: string;
        description: string | null;
        target_date: string | null;
        is_completed: boolean;
        completed_at: string | null;
        sort_order: number;
        created_at: string;
      }>;
      created_at: string;
    }>>(`/api/client/goals${params}`, { token: sessionToken });
  },

  getGoal: (sessionToken: string, goalId: string) =>
    fetchApi<{
      id: string;
      title: string;
      description: string | null;
      category: string | null;
      status: string;
      target_date: string | null;
      progress_percent: number;
      milestones: Array<{
        id: string;
        goal_id: string;
        title: string;
        description: string | null;
        target_date: string | null;
        is_completed: boolean;
        completed_at: string | null;
        sort_order: number;
        created_at: string;
      }>;
      created_at: string;
    }>(`/api/client/goals/${goalId}`, { token: sessionToken }),

  completeMilestone: (
    sessionToken: string,
    goalId: string,
    milestoneId: string,
    isCompleted: boolean
  ) =>
    fetchApi<{
      id: string;
      goal_id: string;
      title: string;
      description: string | null;
      target_date: string | null;
      is_completed: boolean;
      completed_at: string | null;
      sort_order: number;
      created_at: string;
    }>(`/api/client/goals/${goalId}/milestones/${milestoneId}/complete`, {
      method: "PUT",
      body: JSON.stringify({ is_completed: isCompleted }),
      token: sessionToken,
    }),

  getGoalsStats: (sessionToken: string) =>
    fetchApi<{ active_goals: number; completed_goals: number }>(
      "/api/client/goals/stats/summary",
      { token: sessionToken }
    ),

  // Timeline
  getTimeline: (
    sessionToken: string,
    params?: {
      start_date?: string;
      end_date?: string;
      event_types?: string; // comma-separated: goals,sessions,action_items,notes,contracts
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append("start_date", params.start_date);
    if (params?.end_date) queryParams.append("end_date", params.end_date);
    if (params?.event_types) queryParams.append("event_types", params.event_types);
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{
      events: Array<{
        id: string;
        type: string;
        title: string;
        description: string | null;
        date: string;
        icon: string;
        color: string;
      }>;
    }>(`/api/client/timeline${query}`, { token: sessionToken });
  },

  // Onboarding Assessment
  getOnboardingAssessment: (sessionToken: string) =>
    fetchApi<OnboardingAssessmentResponse>("/api/client/onboarding-assessment", {
      token: sessionToken,
    }),
};

// Admin Content Management API
export interface Content {
  id: string;
  title: string;
  description: string | null;
  content_type: string;
  file_url: string | null;
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  external_url: string | null;
  contact_id: string | null;
  contact_name: string | null;
  organization_id: string | null;
  organization_name: string | null;
  project_id: string | null;
  project_name: string | null;
  release_date: string | null;
  is_released: boolean;
  is_active: boolean;
  sort_order: number;
  category: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentCreate {
  title: string;
  description?: string;
  content_type: string;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  external_url?: string;
  contact_id?: string;
  organization_id?: string;
  project_id?: string;
  release_date?: string;
  is_active?: boolean;
  sort_order?: number;
  category?: string;
}

export interface ContentUpdate {
  title?: string;
  description?: string;
  content_type?: string;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  external_url?: string;
  contact_id?: string | null;
  organization_id?: string | null;
  project_id?: string | null;
  release_date?: string | null;
  is_active?: boolean;
  sort_order?: number;
  category?: string;
}

export const contentApi = {
  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      search?: string;
      content_type?: string;
      category?: string;
      contact_id?: string;
      organization_id?: string;
      project_id?: string;
      is_active?: boolean;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.search) queryParams.append("search", params.search);
    if (params?.content_type) queryParams.append("content_type", params.content_type);
    if (params?.category) queryParams.append("category", params.category);
    if (params?.contact_id) queryParams.append("contact_id", params.contact_id);
    if (params?.organization_id) queryParams.append("organization_id", params.organization_id);
    if (params?.project_id) queryParams.append("project_id", params.project_id);
    if (params?.is_active !== undefined) queryParams.append("is_active", params.is_active.toString());
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{ items: Content[]; total: number; page: number; size: number }>(
      `/api/content${query}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<Content>(`/api/content/${id}`, { token }),

  create: (token: string, data: ContentCreate) =>
    fetchApi<Content>("/api/content", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (token: string, id: string, data: ContentUpdate) =>
    fetchApi<Content>(`/api/content/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/content/${id}`, {
      method: "DELETE",
      token,
    }),

  getCategories: (token: string) =>
    fetchApi<{ categories: string[] }>("/api/content/categories", { token }),
};

// Admin Notes API
export interface Note {
  id: string;
  contact_id: string;
  contact_name: string;
  content: string;
  direction: "to_coach" | "to_client";
  parent_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  replies: Note[];
}

export const notesApi = {
  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      contact_id?: string;
      direction?: string;
      is_read?: boolean;
      search?: string;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.contact_id) queryParams.append("contact_id", params.contact_id);
    if (params?.direction) queryParams.append("direction", params.direction);
    if (params?.is_read !== undefined) queryParams.append("is_read", params.is_read.toString());
    if (params?.search) queryParams.append("search", params.search);
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{ items: Note[]; total: number; page: number; size: number }>(
      `/api/notes${query}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<Note>(`/api/notes/${id}`, { token }),

  create: (token: string, data: { contact_id: string; content: string }) =>
    fetchApi<Note>("/api/notes", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  reply: (token: string, noteId: string, content: string) =>
    fetchApi<Note>(`/api/notes/${noteId}/reply`, {
      method: "POST",
      body: JSON.stringify({ content }),
      token,
    }),

  markAsRead: (token: string, id: string) =>
    fetchApi<Note>(`/api/notes/${id}/read`, {
      method: "PUT",
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/notes/${id}`, {
      method: "DELETE",
      token,
    }),

  getUnreadCount: (token: string) =>
    fetchApi<{ count: number }>("/api/notes/unread-count", { token }),
};

// Admin Action Items API
export interface ActionItem {
  id: string;
  contact_id: string;
  contact_name: string;
  session_id: string | null;
  title: string;
  description: string | null;
  due_date: string | null;
  priority: "low" | "medium" | "high";
  status: "pending" | "in_progress" | "completed" | "skipped";
  completed_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export const actionItemsApi = {
  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      contact_id?: string;
      status?: string;
      priority?: string;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.contact_id) queryParams.append("contact_id", params.contact_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.priority) queryParams.append("priority", params.priority);
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{ items: ActionItem[]; total: number; page: number; size: number }>(
      `/api/action-items${query}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<ActionItem>(`/api/action-items/${id}`, { token }),

  create: (
    token: string,
    data: {
      contact_id: string;
      title: string;
      description?: string;
      due_date?: string;
      priority?: "low" | "medium" | "high";
      session_id?: string;
    }
  ) =>
    fetchApi<ActionItem>("/api/action-items", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (
    token: string,
    id: string,
    data: {
      title?: string;
      description?: string;
      due_date?: string;
      priority?: "low" | "medium" | "high";
      status?: "pending" | "in_progress" | "completed" | "skipped";
    }
  ) =>
    fetchApi<ActionItem>(`/api/action-items/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/action-items/${id}`, {
      method: "DELETE",
      token,
    }),
};

// Goals types
export interface GoalMilestone {
  id: string;
  goal_id: string;
  title: string;
  description: string | null;
  target_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  sort_order: number;
  created_at: string;
}

export interface Goal {
  id: string;
  contact_id: string;
  contact_name: string;
  title: string;
  description: string | null;
  category: string | null;
  status: "active" | "completed" | "abandoned";
  target_date: string | null;
  completed_at: string | null;
  progress_percent: number;
  milestones: GoalMilestone[];
  created_at: string;
  updated_at: string;
}

// Admin Goals API
export const goalsApi = {
  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      contact_id?: string;
      status?: string;
      category?: string;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.contact_id) queryParams.append("contact_id", params.contact_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.category) queryParams.append("category", params.category);
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{ items: Goal[]; total: number; page: number; size: number }>(
      `/api/goals${query}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<Goal>(`/api/goals/${id}`, { token }),

  create: (
    token: string,
    data: {
      contact_id: string;
      title: string;
      description?: string;
      category?: string;
      target_date?: string;
      milestones?: Array<{
        title: string;
        description?: string;
        target_date?: string;
        sort_order?: number;
      }>;
    }
  ) =>
    fetchApi<Goal>("/api/goals", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (
    token: string,
    id: string,
    data: {
      title?: string;
      description?: string;
      category?: string;
      target_date?: string;
      status?: "active" | "completed" | "abandoned";
    }
  ) =>
    fetchApi<Goal>(`/api/goals/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/goals/${id}`, {
      method: "DELETE",
      token,
    }),

  // Milestone operations
  addMilestone: (
    token: string,
    goalId: string,
    data: {
      title: string;
      description?: string;
      target_date?: string;
      sort_order?: number;
    }
  ) =>
    fetchApi<GoalMilestone>(`/api/goals/${goalId}/milestones`, {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  updateMilestone: (
    token: string,
    goalId: string,
    milestoneId: string,
    data: {
      title?: string;
      description?: string;
      target_date?: string;
      sort_order?: number;
      is_completed?: boolean;
    }
  ) =>
    fetchApi<GoalMilestone>(`/api/goals/${goalId}/milestones/${milestoneId}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  deleteMilestone: (token: string, goalId: string, milestoneId: string) =>
    fetchApi<void>(`/api/goals/${goalId}/milestones/${milestoneId}`, {
      method: "DELETE",
      token,
    }),
};

// Testimonial types
export interface Testimonial {
  id: string;
  contact_id: string | null;
  organization_id: string | null;
  contact_name: string | null;
  organization_name: string | null;
  video_url: string | null;
  video_public_id: string | null;
  video_duration_seconds: number | null;
  thumbnail_url: string | null;
  quote: string | null;
  transcript: string | null;
  author_name: string;
  author_title: string | null;
  author_company: string | null;
  author_photo_url: string | null;
  permission_granted: boolean;
  status: "pending" | "approved" | "rejected";
  featured: boolean;
  display_order: number;
  request_token: string;
  request_sent_at: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  has_video: boolean;
  created_at: string;
  updated_at: string;
}

// Admin Testimonials API
export const testimonialsApi = {
  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      contact_id?: string;
      organization_id?: string;
      status?: string;
      featured?: boolean;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.contact_id) queryParams.append("contact_id", params.contact_id);
    if (params?.organization_id) queryParams.append("organization_id", params.organization_id);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.featured !== undefined) queryParams.append("featured", params.featured.toString());
    const query = queryParams.toString() ? `?${queryParams.toString()}` : "";
    return fetchApi<{ items: Testimonial[]; total: number; page: number; size: number }>(
      `/api/testimonials${query}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<Testimonial>(`/api/testimonials/${id}`, { token }),

  create: (
    token: string,
    data: {
      contact_id?: string;
      organization_id?: string;
      author_name: string;
      author_title?: string;
      author_company?: string;
      quote?: string;
    }
  ) =>
    fetchApi<Testimonial>("/api/testimonials", {
      method: "POST",
      body: JSON.stringify(data),
      token,
    }),

  update: (
    token: string,
    id: string,
    data: {
      author_name?: string;
      author_title?: string;
      author_company?: string;
      author_photo_url?: string;
      quote?: string;
      transcript?: string;
      status?: "pending" | "approved" | "rejected";
      featured?: boolean;
      display_order?: number;
    }
  ) =>
    fetchApi<Testimonial>(`/api/testimonials/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
      token,
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/testimonials/${id}`, {
      method: "DELETE",
      token,
    }),

  sendRequest: (token: string, id: string, customMessage?: string) =>
    fetchApi<Testimonial>(`/api/testimonials/${id}/send`, {
      method: "POST",
      body: JSON.stringify({ custom_message: customMessage }),
      token,
    }),
};

// Public Testimonials API (no auth required)
export const publicTestimonialsApi = {
  getGallery: (organizationId?: string) => {
    const params = organizationId ? `?organization_id=${organizationId}` : "";
    return fetchApi<{
      featured: Array<{
        id: string;
        author_name: string;
        author_title: string | null;
        author_company: string | null;
        author_photo_url: string | null;
        quote: string | null;
        video_url: string | null;
        thumbnail_url: string | null;
        video_duration_seconds: number | null;
        featured: boolean;
      }>;
      items: Array<{
        id: string;
        author_name: string;
        author_title: string | null;
        author_company: string | null;
        author_photo_url: string | null;
        quote: string | null;
        video_url: string | null;
        thumbnail_url: string | null;
        video_duration_seconds: number | null;
        featured: boolean;
      }>;
      total: number;
    }>(`/api/testimonials/public${params}`);
  },

  getRequest: (token: string) =>
    fetchApi<{
      id: string;
      author_name: string;
      author_title: string | null;
      author_company: string | null;
      status: string;
      already_submitted: boolean;
    }>(`/api/testimonial/${token}`),

  submit: (
    token: string,
    data: {
      author_name: string;
      author_title?: string;
      author_company?: string;
      author_photo_url?: string;
      quote?: string;
      video_url: string;
      video_public_id: string;
      video_duration_seconds?: number;
      thumbnail_url?: string;
      permission_granted: boolean;
    }
  ) =>
    fetchApi<{ id: string; message: string }>(`/api/testimonial/${token}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getUploadSignature: () =>
    fetchApi<{
      signature: string;
      timestamp: number;
      cloud_name: string;
      api_key: string;
      folder: string;
    }>("/api/upload/video/signature"),

  uploadVideo: async (file: File): Promise<{
    url: string;
    public_id: string;
    duration: number;
    thumbnail_url: string | null;
  }> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/api/upload/video`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  },
};

// Onboarding Assessment API (Public)
export interface OnboardingAssessmentPublicData {
  contact_name: string;
  contact_email: string | null;
  already_completed: boolean;
}

export interface OnboardingAssessmentSubmission {
  // Section 1: Client Context
  name_pronouns?: string;
  phone?: string;
  role_title?: string;
  organization_industry?: string;
  time_in_role?: string;
  role_description?: string;
  coaching_motivations?: string[];

  // Section 2: Self Assessment
  confidence_leadership?: number;
  feeling_respected?: number;
  clear_goals_short_term?: number;
  clear_goals_long_term?: number;
  work_life_balance?: number;
  stress_management?: number;
  access_mentors?: number;
  navigate_bias?: number;
  communication_effectiveness?: number;
  taking_up_space?: number;
  team_advocacy?: number;
  career_satisfaction?: number;
  priority_focus_areas?: string;

  // Section 3: Identity & Workplace
  workplace_experience?: string;
  self_doubt_patterns?: string;
  habits_to_shift?: string;

  // Section 4: Goals for Coaching
  coaching_goal?: string;
  success_evidence?: string;
  thriving_vision?: string;

  // Section 5: Wellbeing & Support
  commitment_time?: number;
  commitment_energy?: number;
  commitment_focus?: number;
  potential_barriers?: string;
  support_needed?: string;
  feedback_preference?: string;
  sensitive_topics?: string;

  // Section 6: Logistics
  scheduling_preferences?: string;
}

export interface OnboardingAssessmentResponse extends OnboardingAssessmentSubmission {
  id: string;
  contact_id: string;
  token: string;
  email_sent_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  contact_name?: string;
  contact_email?: string;
}

export const publicOnboardingApi = {
  getAssessment: (token: string) =>
    fetchApi<OnboardingAssessmentPublicData>(`/api/onboarding/${token}`),

  submitAssessment: (token: string, data: OnboardingAssessmentSubmission) =>
    fetchApi<{ success: boolean; message: string }>(`/api/onboarding/${token}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// Onboarding Assessment API (Admin)
export const onboardingAssessmentsApi = {
  list: (token: string, status?: "completed" | "pending") =>
    fetchApi<{
      id: string;
      contact_id: string;
      contact_name: string;
      contact_email: string | null;
      completed_at: string | null;
      email_sent_at: string | null;
      created_at: string;
    }[]>(`/api/onboarding-assessments${status ? `?status=${status}` : ""}`, { token }),

  get: (token: string, assessmentId: string) =>
    fetchApi<OnboardingAssessmentResponse>(`/api/onboarding-assessments/${assessmentId}`, { token }),

  getForContact: (token: string, contactId: string) =>
    fetchApi<OnboardingAssessmentResponse | null>(`/api/contacts/${contactId}/onboarding`, { token }),

  createForContact: (token: string, contactId: string) =>
    fetchApi<{ id: string; token: string; assessment_url: string }>(
      `/api/contacts/${contactId}/onboarding/create`,
      { method: "POST", token }
    ),

  resendEmail: (token: string, contactId: string) =>
    fetchApi<{ success: boolean; message: string }>(
      `/api/contacts/${contactId}/onboarding/resend`,
      { method: "POST", token }
    ),
};

// ICF Tracker Types
export interface CoachingSession {
  id: string;
  contact_id: string | null;
  client_name: string;
  client_email: string | null;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  duration_hours: number;
  session_type: "individual" | "group";
  group_size: number | null;
  payment_type: "paid" | "pro_bono";
  source: string;
  external_id: string | null;
  meeting_title: string | null;
  notes: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  contact_name: string | null;
}

export interface ICFSummary {
  total_hours: number;
  paid_hours: number;
  pro_bono_hours: number;
  individual_hours: number;
  group_hours: number;
  total_sessions: number;
  total_clients: number;
  verified_hours: number;
  unverified_hours: number;
}

export interface ClientHoursSummary {
  client_name: string;
  contact_id: string | null;
  total_sessions: number;
  total_hours: number;
  paid_hours: number;
  pro_bono_hours: number;
  individual_hours: number;
  group_hours: number;
  first_session: string | null;
  last_session: string | null;
}

export interface CoachingSessionCreate {
  contact_id?: string | null;
  client_name: string;
  client_email?: string | null;
  session_date: string;
  start_time?: string | null;
  end_time?: string | null;
  duration_hours: number;
  session_type?: "individual" | "group";
  group_size?: number | null;
  payment_type?: "paid" | "pro_bono";
  source?: string;
  external_id?: string | null;
  meeting_title?: string | null;
  notes?: string | null;
  is_verified?: boolean;
}

export interface ICFRequirements {
  acc_training_required: number;
  acc_coaching_hours_required: number;
  acc_paid_hours_required: number;
  acc_clients_required: number;
  acc_mentor_hours_required: number;
  acc_mentor_individual_required: number;
  acc_mentor_group_max: number;
  pcc_training_required: number;
  pcc_coaching_hours_required: number;
  pcc_paid_hours_required: number;
  pcc_clients_required: number;
  pcc_mentor_hours_required: number;
  pcc_mentor_individual_required: number;
  pcc_mentor_group_max: number;
  mcc_training_required: number;
  mcc_coaching_hours_required: number;
  mcc_paid_hours_required: number;
  mcc_clients_required: number;
  mcc_mentor_hours_required: number;
  mcc_mentor_individual_required: number;
  mcc_mentor_group_max: number;
}

export interface ICFCertificationProgress {
  id: string;
  acc_training_hours: number;
  acc_training_provider?: string | null;
  acc_training_completed: boolean;
  acc_training_completion_date?: string | null;
  acc_training_certificate_url?: string | null;
  pcc_training_hours: number;
  pcc_training_provider?: string | null;
  pcc_training_completed: boolean;
  pcc_training_completion_date?: string | null;
  pcc_training_certificate_url?: string | null;
  acc_mentor_hours: number;
  acc_mentor_individual_hours: number;
  acc_mentor_group_hours: number;
  acc_mentor_name?: string | null;
  acc_mentor_credential?: string | null;
  acc_mentor_completed: boolean;
  pcc_mentor_hours: number;
  pcc_mentor_individual_hours: number;
  pcc_mentor_group_hours: number;
  pcc_mentor_name?: string | null;
  pcc_mentor_credential?: string | null;
  pcc_mentor_completed: boolean;
  acc_exam_passed: boolean;
  acc_exam_date?: string | null;
  acc_exam_score?: number | null;
  pcc_exam_passed: boolean;
  pcc_exam_date?: string | null;
  pcc_exam_score?: number | null;
  acc_applied: boolean;
  acc_application_date?: string | null;
  acc_credential_received: boolean;
  acc_credential_date?: string | null;
  acc_credential_number?: string | null;
  acc_expiration_date?: string | null;
  pcc_applied: boolean;
  pcc_application_date?: string | null;
  pcc_credential_received: boolean;
  pcc_credential_date?: string | null;
  pcc_credential_number?: string | null;
  pcc_expiration_date?: string | null;
  mcc_training_hours: number;
  mcc_training_provider?: string | null;
  mcc_training_completed: boolean;
  mcc_training_completion_date?: string | null;
  mcc_training_certificate_url?: string | null;
  mcc_mentor_hours: number;
  mcc_mentor_individual_hours: number;
  mcc_mentor_group_hours: number;
  mcc_mentor_name?: string | null;
  mcc_mentor_completed: boolean;
  mcc_exam_passed: boolean;
  mcc_exam_date?: string | null;
  mcc_exam_score?: number | null;
  mcc_applied: boolean;
  mcc_application_date?: string | null;
  mcc_credential_received: boolean;
  mcc_credential_date?: string | null;
  mcc_credential_number?: string | null;
  mcc_expiration_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ICFCertificationDashboard {
  total_coaching_hours: number;
  paid_coaching_hours: number;
  pro_bono_hours: number;
  total_clients: number;
  requirements: ICFRequirements;
  acc_training_progress: number;
  acc_coaching_progress: number;
  acc_paid_progress: number;
  acc_clients_progress: number;
  acc_mentor_progress: number;
  acc_ready: boolean;
  pcc_training_progress: number;
  pcc_coaching_progress: number;
  pcc_paid_progress: number;
  pcc_clients_progress: number;
  pcc_mentor_progress: number;
  pcc_ready: boolean;
  mcc_training_progress: number;
  mcc_coaching_progress: number;
  mcc_paid_progress: number;
  mcc_clients_progress: number;
  mcc_mentor_progress: number;
  mcc_ready: boolean;
  progress: ICFCertificationProgress;
}

// ICF Tracker API
export const icfTrackerApi = {
  getSummary: (token: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    return fetchApi<ICFSummary>(`/api/icf-tracker/summary?${params}`, { token });
  },

  getByClient: (token: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    return fetchApi<ClientHoursSummary[]>(`/api/icf-tracker/by-client?${params}`, { token });
  },

  list: (
    token: string,
    params?: {
      page?: number;
      size?: number;
      client_name?: string;
      contact_id?: string;
      session_type?: string;
      payment_type?: string;
      start_date?: string;
      end_date?: string;
      is_verified?: boolean;
    }
  ) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.size) searchParams.set("size", params.size.toString());
    if (params?.client_name) searchParams.set("client_name", params.client_name);
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.session_type) searchParams.set("session_type", params.session_type);
    if (params?.payment_type) searchParams.set("payment_type", params.payment_type);
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);
    if (params?.is_verified !== undefined) searchParams.set("is_verified", params.is_verified.toString());
    return fetchApi<{ items: CoachingSession[]; total: number; page: number; size: number }>(
      `/api/icf-tracker?${searchParams}`,
      { token }
    );
  },

  get: (token: string, id: string) =>
    fetchApi<CoachingSession>(`/api/icf-tracker/${id}`, { token }),

  create: (token: string, data: CoachingSessionCreate) =>
    fetchApi<CoachingSession>("/api/icf-tracker", {
      method: "POST",
      token,
      body: JSON.stringify(data),
    }),

  update: (token: string, id: string, data: Partial<CoachingSessionCreate>) =>
    fetchApi<CoachingSession>(`/api/icf-tracker/${id}`, {
      method: "PUT",
      token,
      body: JSON.stringify(data),
    }),

  delete: (token: string, id: string) =>
    fetchApi<void>(`/api/icf-tracker/${id}`, {
      method: "DELETE",
      token,
    }),

  bulkImport: (token: string, sessions: CoachingSessionCreate[]) =>
    fetchApi<{ imported: number; skipped: number; errors: string[] }>("/api/icf-tracker/bulk-import", {
      method: "POST",
      token,
      body: JSON.stringify({ sessions }),
    }),

  verifyAll: (token: string, clientName?: string) => {
    const params = new URLSearchParams();
    if (clientName) params.set("client_name", clientName);
    return fetchApi<{ verified: number }>(`/api/icf-tracker/verify-all?${params}`, {
      method: "POST",
      token,
    });
  },

  matchContacts: (token: string) =>
    fetchApi<{ matched: number; total_unlinked: number }>("/api/icf-tracker/match-contacts", {
      method: "POST",
      token,
    }),

  exportCSV: (token: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    // Return the URL for direct download
    return `${API_URL}/api/icf-tracker/export/csv?${params}`;
  },

  // Certification Progress
  getCertificationDashboard: (token: string) =>
    fetchApi<ICFCertificationDashboard>("/api/icf-tracker/certification/dashboard", { token }),

  getCertificationProgress: (token: string) =>
    fetchApi<ICFCertificationProgress>("/api/icf-tracker/certification/progress", { token }),

  updateCertificationProgress: (token: string, data: Partial<ICFCertificationProgress>) =>
    fetchApi<ICFCertificationProgress>("/api/icf-tracker/certification/progress", {
      method: "PUT",
      token,
      body: JSON.stringify(data),
    }),
};
