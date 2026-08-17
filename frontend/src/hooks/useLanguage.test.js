import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useLanguage } from "./useLanguage";

describe("useLanguage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults to English when nothing is stored", () => {
    const { result } = renderHook(() => useLanguage());
    expect(result.current[0]).toBe("en");
  });

  it("reads a previously stored language", () => {
    localStorage.setItem("bodhi_language", "ta");
    const { result } = renderHook(() => useLanguage());
    expect(result.current[0]).toBe("ta");
  });

  it("persists the language across hook instances", () => {
    const { result } = renderHook(() => useLanguage());
    act(() => result.current[1]("ta"));

    expect(result.current[0]).toBe("ta");
    expect(localStorage.getItem("bodhi_language")).toBe("ta");

    const { result: result2 } = renderHook(() => useLanguage());
    expect(result2.current[0]).toBe("ta");
  });
});
