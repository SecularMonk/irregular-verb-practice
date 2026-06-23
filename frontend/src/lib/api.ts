import { ANONYMOUS_ID_HEADER, readStoredAnonymousId, storeAnonymousId } from "./identity";

export type ExerciseType = "fill_blank";

export interface ExerciseResponse {
  id: string;
  exercise_type: ExerciseType;
  difficulty: number;
  prompt: string;
}

export interface AttemptResponse {
  is_correct: boolean;
  corrected_answer: string;
  explanation: string;
}

export interface DifficultyProgress {
  attempts: number;
  correct_answers: number;
  success_rate: number;
}

export interface RecentAttempt {
  attempt_id: string;
  exercise_id: string;
  prompt: string;
  difficulty: number;
  user_answer: string;
  is_correct: boolean;
  corrected_answer: string;
  explanation: string;
  timestamp: string;
}

export interface ProgressResponse {
  overall_attempts: number;
  correct_answers: number;
  success_rate: number;
  by_difficulty: Record<string, DifficultyProgress>;
  recent_attempts: RecentAttempt[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function buildHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const fallbackId = readStoredAnonymousId();
  if (fallbackId) {
    headers[ANONYMOUS_ID_HEADER] = fallbackId;
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...buildHeaders(),
      ...(init?.headers || {}),
    },
    credentials: "include",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function ensureSession(): Promise<string> {
  const payload = await request<{ user_id: string }>("/api/session", {
    method: "POST",
  });
  storeAnonymousId(payload.user_id);
  return payload.user_id;
}

export async function createExercise(difficulty: number): Promise<ExerciseResponse> {
  return request<ExerciseResponse>("/api/exercise", {
    method: "POST",
    body: JSON.stringify({
      difficulty,
      exercise_type: "fill_blank",
    }),
  });
}

export async function submitAttempt(
  exerciseId: string,
  userAnswer: string,
): Promise<AttemptResponse> {
  return request<AttemptResponse>("/api/attempt", {
    method: "POST",
    body: JSON.stringify({
      exercise_id: exerciseId,
      user_answer: userAnswer,
    }),
  });
}

export async function getProgress(): Promise<ProgressResponse> {
  return request<ProgressResponse>("/api/progress");
}
