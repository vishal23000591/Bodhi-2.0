import "@testing-library/jest-dom/vitest";

// jsdom's built-in localStorage is unreliable across Node/jsdom version
// combinations (Node 22+ also ships an experimental global `localStorage`
// that can shadow it) — a small deterministic in-memory polyfill sidesteps
// both issues for tests.
class MemoryStorage {
  constructor() {
    this.store = new Map();
  }
  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }
  setItem(key, value) {
    this.store.set(key, String(value));
  }
  removeItem(key) {
    this.store.delete(key);
  }
  clear() {
    this.store.clear();
  }
}

const storage = new MemoryStorage();
Object.defineProperty(globalThis, "localStorage", { value: storage, configurable: true });
if (typeof window !== "undefined") {
  Object.defineProperty(window, "localStorage", { value: storage, configurable: true });
}
