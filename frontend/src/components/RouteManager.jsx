import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

// Maps the current path to a human page name (most specific first).
const TITLES = [
  [/^\/login/, "Log in"],
  [/^\/register/, "Create account"],
  [/^\/quiz\//, "Quiz"],
  [/^\/results\//, "Results"],
  [/^\/history/, "My attempts"],
  [/^\/admin\/questions\/new/, "New question"],
  [/^\/admin\/questions\/\d+\/edit/, "Edit question"],
  [/^\/admin\/questions/, "Question bank"],
  [/^\/admin\/review/, "Review queue"],
  [/^\/$/, "Home"],
];

function pageName(pathname) {
  for (const [re, name] of TITLES) if (re.test(pathname)) return name;
  return "Quiz Platform";
}

// On each navigation: update the document title, announce the new page to
// screen readers (aria-live), and move keyboard focus to the main region so
// the next Tab starts from the page content rather than the top of the app.
export default function RouteManager() {
  const { pathname } = useLocation();
  const [announcement, setAnnouncement] = useState("");
  const firstRender = useRef(true);

  useEffect(() => {
    const name = pageName(pathname);
    document.title = `${name} · Quiz Platform`;
    setAnnouncement(`${name} page`);

    // Don't steal focus on the very first load.
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    const main = document.getElementById("main-content");
    if (main) main.focus();
  }, [pathname]);

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
      data-testid="route-announcer"
    >
      {announcement}
    </div>
  );
}
