import api from "./client.js";

export const startAttempt = () =>
  api.post("/api/attempts/", {}).then((r) => r.data);

export const getAttempt = (id) =>
  api.get(`/api/attempts/${id}/`).then((r) => r.data);

export const listAttempts = () =>
  api.get("/api/attempts/").then((r) => r.data);

// answers: [{ attempt_question, text_value?, numeric_value?, selected_choice_ids? }]
// images: { [attempt_question_id]: File }
export function submitAttempt(id, answers, images = {}) {
  const form = new FormData();
  form.append("answers", JSON.stringify(answers));
  for (const [aqId, file] of Object.entries(images)) {
    if (file) form.append(`image_${aqId}`, file);
  }
  return api
    .post(`/api/attempts/${id}/submit/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
}
