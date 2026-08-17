import { describe, expect, it } from "vitest";
import { groupChatsByRecency, groupLabel } from "./dateGroups";

// Constructed with the local-time Date constructor (not ISO/UTC strings) so
// this test is not sensitive to the machine's timezone offset.
const NOW = new Date(2026, 7, 18, 12, 0, 0); // Aug 18, 2026, local noon

function localDate(day, hour = 12) {
  return new Date(2026, 7, day, hour, 0, 0);
}

describe("groupLabel", () => {
  it("labels same-day timestamps as Today", () => {
    expect(groupLabel(localDate(18, 1), NOW)).toBe("Today");
  });

  it("labels yesterday correctly", () => {
    expect(groupLabel(localDate(17, 23), NOW)).toBe("Yesterday");
  });

  it("labels within the last 7 days as This week", () => {
    expect(groupLabel(localDate(13), NOW)).toBe("This week");
  });

  it("labels anything older as Older", () => {
    expect(groupLabel(localDate(1), NOW)).toBe("Older");
  });
});

describe("groupChatsByRecency", () => {
  it("groups and orders chats Today -> Yesterday -> This week -> Older", () => {
    const chats = [
      { id: "1", title: "Old chapter", last_message_at: localDate(1) },
      { id: "2", title: "Today's chat", last_message_at: localDate(18, 2) },
      { id: "3", title: "Yesterday's chat", last_message_at: localDate(17, 20) },
    ];
    const groups = groupChatsByRecency(chats, NOW);
    expect(groups.map(([label]) => label)).toEqual(["Today", "Yesterday", "Older"]);
    expect(groups[0][1][0].title).toBe("Today's chat");
  });

  it("returns an empty list for no chats", () => {
    expect(groupChatsByRecency([], NOW)).toEqual([]);
  });
});
