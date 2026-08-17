import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ChatBubble from "./ChatBubble";

describe("ChatBubble", () => {
  it("renders a user message without a source chip", () => {
    render(<ChatBubble message={{ id: "1", role: "user", content: "Why do plants need water?" }} />);
    expect(screen.getByText("Why do plants need water?")).toBeInTheDocument();
    expect(screen.queryByText(/📖/)).not.toBeInTheDocument();
  });

  it("renders an assistant message with source chips", () => {
    render(
      <ChatBubble
        message={{
          id: "2",
          role: "assistant",
          content: "Plants absorb water through their roots.",
          sources: [{ page: 12 }, { page: 13 }],
        }}
      />
    );
    expect(screen.getByText("Plants absorb water through their roots.")).toBeInTheDocument();
    expect(screen.getByText("📖 p.12")).toBeInTheDocument();
    expect(screen.getByText("📖 p.13")).toBeInTheDocument();
  });
});
