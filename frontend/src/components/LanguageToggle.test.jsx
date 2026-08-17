import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import LanguageToggle from "./LanguageToggle";

describe("LanguageToggle", () => {
  it("marks the current language as active", () => {
    render(<LanguageToggle language="ta" onChange={() => {}} />);
    expect(screen.getByText("தமிழ்")).toHaveClass("active");
    expect(screen.getByText("EN")).not.toHaveClass("active");
  });

  it("calls onChange with the clicked language code", () => {
    const onChange = vi.fn();
    render(<LanguageToggle language="en" onChange={onChange} />);
    fireEvent.click(screen.getByText("தமிழ்"));
    expect(onChange).toHaveBeenCalledWith("ta");
  });

  it("offers a Tanglish option alongside English and Tamil", () => {
    const onChange = vi.fn();
    render(<LanguageToggle language="tanglish" onChange={onChange} />);
    expect(screen.getByText("Tanglish")).toHaveClass("active");
    fireEvent.click(screen.getByText("EN"));
    expect(onChange).toHaveBeenCalledWith("en");
  });
});
