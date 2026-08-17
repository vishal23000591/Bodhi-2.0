const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "bodhi_access_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 204) return null;

  let data = null;
  try {
    data = await resp.json();
  } catch {
    data = null;
  }

  if (!resp.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : `Request failed (${resp.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  signup: (payload) => request("/auth/signup", { method: "POST", body: payload }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload }),
  me: () => request("/auth/me"),

  uploadDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/documents/upload", { method: "POST", body: form, isForm: true });
  },
  documents: () => request("/documents"),
  documentStatus: (documentId) => request(`/documents/${documentId}/status`),
  deleteDocument: (documentId) => request(`/documents/${documentId}`, { method: "DELETE" }),
  topics: (documentId) => request(`/documents/${documentId}/topics`),

  openChat: (payload) => request("/chats", { method: "POST", body: payload }),
  chats: () => request("/chats"),
  chatMessages: (chatId) => request(`/chats/${chatId}/messages`),
  ask: (chatId, message, language = "en") =>
    request(`/chats/${chatId}/ask`, { method: "POST", body: { message, language } }),
  deleteChat: (chatId) => request(`/chats/${chatId}`, { method: "DELETE" }),

  teach: (topicId, language = "en") =>
    request(`/topics/${topicId}/teach?language=${language}`, { method: "POST" }),
  teachbackQuestion: (topicId, language = "en") =>
    request(`/topics/${topicId}/teachback/question?language=${language}`, { method: "POST" }),
  teachbackAnswer: (topicId, answer, language = "en") =>
    request(`/topics/${topicId}/teachback/answer`, { method: "POST", body: { answer, language } }),
  mastery: (topicId) => request(`/topics/${topicId}/mastery`),

  generatePractice: (topicId, language = "en") =>
    request(`/topics/${topicId}/practice/generate?language=${language}`, { method: "POST" }),
  submitPractice: (practiceId, payload) =>
    request(`/practice/${practiceId}/submit`, { method: "POST", body: payload }),
};
