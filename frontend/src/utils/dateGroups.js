const DAY_MS = 86_400_000;

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

/** Groups a timestamp into the ChatGPT/Claude-style sidebar buckets. */
export function groupLabel(dateStr, now = new Date()) {
  const date = new Date(dateStr);
  const diffDays = Math.floor((startOfDay(now) - startOfDay(date)) / DAY_MS);
  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays <= 7) return "This week";
  return "Older";
}

export const GROUP_ORDER = ["Today", "Yesterday", "This week", "Older"];

export function groupChatsByRecency(chats, now = new Date()) {
  const map = {};
  for (const chat of chats) {
    const label = groupLabel(chat.last_message_at, now);
    map[label] = map[label] || [];
    map[label].push(chat);
  }
  return GROUP_ORDER.filter((label) => map[label]?.length).map((label) => [label, map[label]]);
}
