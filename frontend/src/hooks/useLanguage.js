import { useCallback, useState } from "react";

const KEY = "bodhi_language";

/** Persists the student's English/Tamil toggle across sessions. Only the
 * tutoring flows (teach, teach-back, practice, ask-a-doubt) read this —
 * topic titles stay in English since they're generated once at upload. */
export function useLanguage() {
  const [language, setLanguageState] = useState(() => localStorage.getItem(KEY) || "en");

  const setLanguage = useCallback((lang) => {
    localStorage.setItem(KEY, lang);
    setLanguageState(lang);
  }, []);

  return [language, setLanguage];
}
