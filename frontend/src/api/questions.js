import api from "./client.js";

export const QUESTION_TYPES = [
  { value: "text", label: "Text (free response)" },
  { value: "single", label: "Single choice" },
  { value: "multiple", label: "Multiple choice" },
  { value: "numerical", label: "Numerical input" },
  { value: "image", label: "Image upload" },
];

export const DIFFICULTIES = [
  { value: "easy", label: "Easy" },
  { value: "med", label: "Medium" },
  { value: "hard", label: "Hard" },
];

export const typeLabel = (v) =>
  QUESTION_TYPES.find((t) => t.value === v)?.label || v;

export function listQuestions(filters = {}) {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== "" && v != null)
  );
  return api.get("/api/questions/", { params }).then((r) => r.data);
}

export const getQuestion = (id) =>
  api.get(`/api/questions/${id}/`).then((r) => r.data);

export const createQuestion = (payload) =>
  api.post("/api/questions/", payload).then((r) => r.data);

export const updateQuestion = (id, payload) =>
  api.put(`/api/questions/${id}/`, payload).then((r) => r.data);

export const deleteQuestion = (id) => api.delete(`/api/questions/${id}/`);
