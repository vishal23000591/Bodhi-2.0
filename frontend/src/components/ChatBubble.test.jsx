import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import ChatBubble from "./ChatBubble";

function renderBubble(message, props = {}) {
  return render(
    <AuthProvider>
      <ChatBubble message={message} {...props} />
    </AuthProvider>
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe("ChatBubble", () => {
  it("renders a user message without a source chip", () => {
    const { container } = renderBubble({
      id: "1",
      role: "user",
      content: "Why do plants need water?",
      created_at: "2026-08-18T10:42:00+00:00",
    });
    expect(screen.getByText("Why do plants need water?")).toBeInTheDocument();
    expect(container.querySelector(".source-chip")).not.toBeInTheDocument();
  });

  it("renders an assistant message with a Bodhi label and source chips", () => {
    renderBubble({
      id: "2",
      role: "assistant",
      content: "Plants absorb water through their roots.",
      sources: [{ page: 12 }, { page: 13 }],
      created_at: "2026-08-18T10:44:00+00:00",
    });
    expect(screen.getByText("Bodhi")).toBeInTheDocument();
    expect(screen.getByText("Plants absorb water through their roots.")).toBeInTheDocument();
    expect(screen.getByText(/p\.12/)).toBeInTheDocument();
    expect(screen.getByText(/p\.13/)).toBeInTheDocument();
  });

  it("shows an overflow chip when there are more than 4 sources", () => {
    renderBubble({
      id: "3",
      role: "assistant",
      content: "Answer with lots of sources.",
      sources: [{ page: 1 }, { page: 2 }, { page: 3 }, { page: 4 }, { page: 5 }],
    });
    expect(screen.getByText("+1 more")).toBeInTheDocument();
    expect(screen.queryByText(/p\.5/)).not.toBeInTheDocument();
  });
});
