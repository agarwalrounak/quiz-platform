import api from "./client.js";

export const listReviewQueue = () =>
  api.get("/api/review/queue/").then((r) => r.data);

export const submitVerdict = (answerId, isCorrect) =>
  api
    .post(`/api/review/answers/${answerId}/`, { is_correct: isCorrect })
    .then((r) => r.data);
