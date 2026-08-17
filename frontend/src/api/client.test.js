import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, clearToken, getToken, setToken } from "./client";

function mockFetchOnce(status, body) {
  global.fetch = vi.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    json: async () => body,
  });
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("stores and clears the access token", () => {
    expect(getToken()).toBeNull();
    setToken("abc123");
    expect(getToken()).toBe("abc123");
    clearToken();
    expect(getToken()).toBeNull();
  });

  it("attaches the Authorization header when a token is present", async () => {
    setToken("my-token");
    mockFetchOnce(200, { name: "Vishal" });

    await api.me();

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer my-token");
  });

  it("omits the Authorization header when there is no token", async () => {
    mockFetchOnce(200, { access_token: "t", refresh_token: "r" });

    await api.login({ email: "a@b.com", password: "pw" });

    const [, options] = global.fetch.mock.calls[0];
    expect(options.headers.Authorization).toBeUndefined();
  });

  it("throws the server's detail message on error responses", async () => {
    mockFetchOnce(401, { detail: "Invalid email or password" });

    await expect(api.login({ email: "a@b.com", password: "wrong" })).rejects.toThrow(
      "Invalid email or password"
    );
  });

  it("returns null for 204 No Content responses", async () => {
    global.fetch = vi.fn().mockResolvedValue({ status: 204, ok: true });
    const result = await api.deleteChat("chat1");
    expect(result).toBeNull();
  });

  it("defaults ask() to English and includes the message body", async () => {
    mockFetchOnce(200, { id: "m1", role: "assistant", content: "hi" });

    await api.ask("chat1", "why?");

    const [, options] = global.fetch.mock.calls[0];
    expect(JSON.parse(options.body)).toEqual({ message: "why?", language: "en" });
  });

  it("passes the chosen language for ask() and teach()", async () => {
    mockFetchOnce(200, { id: "m1", role: "assistant", content: "hi" });
    await api.ask("chat1", "why?", "ta");
    expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({ message: "why?", language: "ta" });

    mockFetchOnce(200, { explanation: "...", sources: [] });
    await api.teach("topic1", "ta");
    expect(global.fetch.mock.calls[0][0]).toContain("/topics/topic1/teach?language=ta");
  });
});
