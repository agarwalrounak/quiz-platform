import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import LoginPage from "./LoginPage.jsx";
import { AuthProvider } from "./AuthContext.jsx";

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("LoginPage", () => {
  it("renders accessible username and password fields", () => {
    renderPage();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("links to the register page", () => {
    renderPage();
    expect(screen.getByRole("link", { name: /register/i })).toHaveAttribute(
      "href",
      "/register"
    );
  });
});
