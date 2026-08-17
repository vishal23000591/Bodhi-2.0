import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MasteryBadge from "./MasteryBadge";

describe("MasteryBadge", () => {
  it("renders the label for a known status", () => {
    render(<MasteryBadge status="mastered" />);
    expect(screen.getByText("Mastered")).toBeInTheDocument();
  });

  it("falls back to Not Started for an unknown or missing status", () => {
    render(<MasteryBadge status={undefined} />);
    expect(screen.getByText("Not Started")).toBeInTheDocument();
  });

  it("renders needs_reteach as Needs Reteach", () => {
    render(<MasteryBadge status="needs_reteach" />);
    expect(screen.getByText("Needs Reteach")).toBeInTheDocument();
  });
});
