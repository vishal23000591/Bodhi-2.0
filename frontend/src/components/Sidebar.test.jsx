import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { AuthProvider } from "../context/AuthContext";
import Sidebar from "./Sidebar";

vi.mock("../api/client", () => ({
  api: {
    documents: vi.fn(),
    chats: vi.fn(),
    topics: vi.fn(),
    deleteChat: vi.fn(),
    deleteDocument: vi.fn(),
    me: vi.fn(),
  },
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

function renderSidebar(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Sidebar />} />
          <Route path="/documents/:documentId/topics" element={<Sidebar />} />
          <Route path="/documents/:documentId/topics/:topicId" element={<Sidebar />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

const DOC = {
  id: "doc1",
  filename: "Chapter 4 - Photosynthesis.pdf",
  status: "ready",
  created_at: new Date().toISOString(),
};

const TOPICS = [
  { id: "topic1", document_id: "doc1", title: "Photosynthesis", description: "", page_range: [1, 2] },
  { id: "topic2", document_id: "doc1", title: "Respiration", description: "", page_range: [3, 4] },
];

const CHAT = {
  id: "chat1",
  document_id: "doc1",
  topic_id: "topic1",
  title: "Photosynthesis",
  last_message_at: new Date().toISOString(),
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

describe("Sidebar", () => {
  it("shows the document, trimmed of its .pdf extension", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([]);
    api.topics.mockResolvedValue(TOPICS);

    renderSidebar();

    await waitFor(() => expect(screen.getByText("Chapter 4 - Photosynthesis")).toBeInTheDocument());
    expect(screen.queryByText(/\.pdf/i)).not.toBeInTheDocument();
  });

  it("expands to show topics, distinguishing chatted from not-yet-chatted ones", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([CHAT]);
    api.topics.mockResolvedValue(TOPICS);

    renderSidebar();

    const docRow = await screen.findByText("Chapter 4 - Photosynthesis");
    fireEvent.click(docRow.closest(".sidebar-doc-item"));

    const chattedTopic = await screen.findByText("Photosynthesis", { selector: ".sidebar-item-title" });
    const notChattedTopic = screen.getByText("Respiration");

    expect(chattedTopic.closest(".sidebar-topic-item")).toHaveClass("chatted");
    expect(notChattedTopic.closest(".sidebar-topic-item")).toHaveClass("not-chatted");
  });

  it("auto-expands the document for the currently open topic", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([CHAT]);
    api.topics.mockResolvedValue(TOPICS);

    renderSidebar("/documents/doc1/topics/topic1");

    expect(await screen.findByText("Respiration")).toBeInTheDocument();
  });

  it("deletes a chatted topic's chat and refreshes", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([CHAT]);
    api.topics.mockResolvedValue(TOPICS);
    api.deleteChat.mockResolvedValue(null);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderSidebar();
    const docRow = await screen.findByText("Chapter 4 - Photosynthesis");
    fireEvent.click(docRow.closest(".sidebar-doc-item"));

    const chattedTopic = await screen.findByText("Photosynthesis", { selector: ".sidebar-item-title" });
    const deleteBtn = chattedTopic.closest(".sidebar-topic-item").querySelector(".sidebar-item-delete");
    fireEvent.click(deleteBtn);

    await waitFor(() => expect(api.deleteChat).toHaveBeenCalledWith("chat1"));
  });

  it("deletes an entire document after confirmation and navigates away if it was open", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([]);
    api.topics.mockResolvedValue(TOPICS);
    api.deleteDocument.mockResolvedValue(null);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderSidebar("/documents/doc1/topics/topic1");

    const docRow = await screen.findByText("Chapter 4 - Photosynthesis");
    const deleteBtn = docRow.closest(".sidebar-doc-item").querySelector(".sidebar-item-delete");
    fireEvent.click(deleteBtn);

    await waitFor(() => expect(api.deleteDocument).toHaveBeenCalledWith("doc1"));
  });

  it("does not delete the document if the confirmation is declined", async () => {
    api.documents.mockResolvedValue([DOC]);
    api.chats.mockResolvedValue([]);
    api.topics.mockResolvedValue(TOPICS);
    vi.spyOn(window, "confirm").mockReturnValue(false);

    renderSidebar();
    const docRow = await screen.findByText("Chapter 4 - Photosynthesis");
    const deleteBtn = docRow.closest(".sidebar-doc-item").querySelector(".sidebar-item-delete");
    fireEvent.click(deleteBtn);

    expect(api.deleteDocument).not.toHaveBeenCalled();
  });
});
