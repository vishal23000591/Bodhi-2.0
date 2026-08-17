import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import TopicCard from "./TopicCard";

const topic = {
  id: "t1",
  title: "Photosynthesis",
  description: "How plants make food",
  page_range: [10, 14],
};

describe("TopicCard", () => {
  it("renders title, description, and page range", () => {
    render(<TopicCard topic={topic} mastery={null} onClick={() => {}} />);
    expect(screen.getByText("Photosynthesis")).toBeInTheDocument();
    expect(screen.getByText("How plants make food")).toBeInTheDocument();
    expect(screen.getByText("p.10–14")).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(<TopicCard topic={topic} mastery={null} onClick={onClick} />);
    fireEvent.click(screen.getByText("Photosynthesis"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("shows mastery status when provided", () => {
    render(<TopicCard topic={topic} mastery={{ status: "mastered" }} onClick={() => {}} />);
    expect(screen.getByText("Mastered")).toBeInTheDocument();
  });
});
