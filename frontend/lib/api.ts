import { getToken } from "./auth";

export type Scholarship = {
  id: number;
  scheme_id: string;
  scheme_name: string;
  provider: string;
  categories: string[];
  income_ceiling: number | null;
  education_levels: string[];
  state: string;
  benefits: string;
  deadline: string | null;
  eligibility_text: string;
  documents_required: string[];
  application_process: string;
  source_url: string;
};

export type Recommendation = {
  scholarship: Scholarship;
  match_score: number;
  deadline_days_left: number | null;
  reasons: string[];
  missing_or_mismatch: string[];
};

export type SavedScholarship = {
  id: number;
  saved_at: string;
  scholarship: Scholarship;
  deadline_days_left: number | null;
};

export type Dashboard = {
  name: string;
  profile_completion: number;
  top_matches: Recommendation[];
  saved_scholarships: SavedScholarship[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const scholarships: Scholarship[] = [
  {
    id: 1,
    scheme_id: "nsp_merit_punjab",
    scheme_name: "NSP Merit Scholarship",
    provider: "Central",
    categories: ["General", "OBC", "SC", "ST"],
    income_ceiling: 800000,
    education_levels: ["UG", "Engineering"],
    state: "Punjab",
    benefits: "Tuition fee support and maintenance allowance for meritorious undergraduate students.",
    deadline: "2026-08-30",
    eligibility_text:
      "Applicants must be Punjab residents enrolled in a recognised undergraduate or engineering programme with annual family income up to INR 8,00,000.",
    documents_required: ["Aadhaar", "Income certificate", "Punjab domicile certificate", "Previous marksheet", "Bank passbook"],
    application_process:
      "Apply through the National Scholarship Portal, complete Aadhaar verification, upload required documents, and submit through the institution for verification.",
    source_url: "https://scholarships.gov.in/",
  },
  {
    id: 2,
    scheme_id: "aicte_pragati",
    scheme_name: "AICTE Pragati",
    provider: "AICTE",
    categories: ["General", "OBC", "SC", "ST"],
    income_ceiling: 800000,
    education_levels: ["UG", "Diploma", "Engineering"],
    state: "All India",
    benefits: "Financial assistance for girl students admitted to technical degree or diploma courses.",
    deadline: "2026-09-15",
    eligibility_text:
      "Girl students admitted to first year or second year lateral entry of AICTE-approved technical degree or diploma courses may apply. Family income should not exceed INR 8,00,000 per annum.",
    documents_required: ["Income certificate", "Admission letter", "Marksheet", "Bank details", "Aadhaar"],
    application_process:
      "Register on NSP, choose AICTE Pragati, fill academic and bank details, upload documents, and submit for institute verification.",
    source_url: "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions",
  },
  {
    id: 3,
    scheme_id: "ugc_ishan_uday",
    scheme_name: "UGC Scholarship",
    provider: "UGC",
    categories: ["General", "OBC", "SC", "ST"],
    income_ceiling: 450000,
    education_levels: ["UG"],
    state: "All India",
    benefits: "Monthly scholarship support for undergraduate studies in recognised universities and colleges.",
    deadline: "2026-10-10",
    eligibility_text:
      "Students enrolled in undergraduate courses at recognised institutions may apply subject to income and academic eligibility rules listed by UGC.",
    documents_required: ["Income certificate", "Domicile certificate if applicable", "Admission proof", "Previous marksheet", "Bank details"],
    application_process:
      "Apply through NSP or the UGC scholarship portal when applications open, upload documents, and complete institute verification.",
    source_url: "https://www.ugc.gov.in/",
  },
  {
    id: 4,
    scheme_id: "punjab_post_matric_sc",
    scheme_name: "Punjab Post Matric Scholarship for SC Students",
    provider: "State",
    categories: ["SC"],
    income_ceiling: 250000,
    education_levels: ["UG", "PG", "Diploma"],
    state: "Punjab",
    benefits: "Reimbursement of compulsory non-refundable fees and maintenance allowance for eligible SC students.",
    deadline: "2026-07-31",
    eligibility_text:
      "SC students domiciled in Punjab and studying post-matric courses may apply if annual family income is within the notified ceiling.",
    documents_required: ["Caste certificate", "Income certificate", "Punjab domicile certificate", "Fee receipt", "Bank passbook"],
    application_process:
      "Apply on the Punjab scholarship portal, upload required certificates, and route the application through the institution.",
    source_url: "https://scholarships.punjab.gov.in/",
  },
];

export const demoDashboard: Dashboard = {
  name: "Aarushi",
  profile_completion: 90,
  top_matches: [
    recommendation(scholarships[0], 95, 73, ["Punjab Resident", "Engineering Student", "Income Eligible", "Deadline Approaching"]),
    recommendation(scholarships[1], 89, 89, ["Engineering Student", "Income Eligible", "Available Across India"]),
    recommendation(scholarships[2], 84, 114, ["UG Match", "Income Eligible", "Recognised Institution"]),
  ],
  saved_scholarships: [
    {
      id: 1,
      saved_at: "2026-06-18T10:00:00Z",
      scholarship: scholarships[0],
      deadline_days_left: 73,
    },
    {
      id: 2,
      saved_at: "2026-06-18T10:05:00Z",
      scholarship: scholarships[1],
      deadline_days_left: 89,
    },
  ],
};

function recommendation(
  scholarship: Scholarship,
  match_score: number,
  deadline_days_left: number,
  reasons: string[],
): Recommendation {
  return { scholarship, match_score, deadline_days_left, reasons, missing_or_mismatch: [] };
}

export async function getDashboard(): Promise<Dashboard> {
  return getJson<Dashboard>("/dashboard", demoDashboard);
}

export async function getSchemes(): Promise<Scholarship[]> {
  return getJson<Scholarship[]>("/schemes", scholarships);
}

export async function getScheme(schemeId: string): Promise<Scholarship> {
  const fallback = scholarships.find((scheme) => scheme.scheme_id === schemeId) ?? scholarships[0];
  return getJson<Scholarship>(`/schemes/${schemeId}`, fallback);
}

async function getJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: authHeaders(),
      cache: "no-store",
    });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

function authHeaders(): HeadersInit {
  // Read the live token from localStorage (set after login/signup).
  // Falls back gracefully to empty headers when the user is not logged in.
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/* ── Auth API calls ────────────────────────────────────────────────────────── */

export type AuthPayload = { email: string; password: string };
export type AuthToken = { access_token: string; token_type: string };

export async function loginUser(payload: AuthPayload): Promise<AuthToken> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Login failed");
  }
  return (await response.json()) as AuthToken;
}

export async function signupUser(payload: AuthPayload): Promise<AuthToken> {
  const response = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Registration failed");
  }
  return (await response.json()) as AuthToken;
}

export function formatIncome(value: number | null): string {
  if (value === null) return "No ceiling listed";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function supportLabel(scholarship: Scholarship): string {
  const text = `${scholarship.benefits} ${scholarship.scheme_name}`.toLowerCase();
  if (text.includes("pragati")) return "₹50,000 Support";
  if (text.includes("tuition")) return "Tuition Support";
  if (text.includes("monthly")) return "Monthly Aid";
  if (text.includes("maintenance")) return "Fee + Allowance";
  return "Financial Support";
}

export type ChatSource = {
  scheme_id: string;
  scheme_name: string;
  source_url: string;
};

export type ChatResponse = {
  answer: string;
  sources: ChatSource[];
};

export async function saveScholarship(schemeId: string): Promise<SavedScholarship | null> {
  try {
    const response = await fetch(`${API_BASE}/saved/${schemeId}`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!response.ok) return null;
    return (await response.json()) as SavedScholarship;
  } catch {
    return null;
  }
}

export async function unsaveScholarship(schemeId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/saved/${schemeId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const fallback: ChatResponse = {
    answer: "I couldn't reach the advisor. Please check your network connection and try again.",
    sources: [],
  };
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) return fallback;
    return (await response.json()) as ChatResponse;
  } catch {
    return fallback;
  }
}

