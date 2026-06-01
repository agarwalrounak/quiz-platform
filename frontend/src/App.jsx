import { Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import LoginPage from "./auth/LoginPage.jsx";
import RegisterPage from "./auth/RegisterPage.jsx";
import { RequireAdmin, RequireAuth } from "./auth/guards.jsx";
import Dashboard from "./player/Dashboard.jsx";
import QuizPlayer from "./player/QuizPlayer.jsx";
import ResultsPage from "./results/ResultsPage.jsx";
import HistoryPage from "./results/HistoryPage.jsx";
import QuestionList from "./admin/QuestionList.jsx";
import QuestionEditor from "./admin/QuestionEditor.jsx";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/quiz/:id"
          element={
            <RequireAuth>
              <QuizPlayer />
            </RequireAuth>
          }
        />
        <Route
          path="/history"
          element={
            <RequireAuth>
              <HistoryPage />
            </RequireAuth>
          }
        />
        <Route
          path="/results/:id"
          element={
            <RequireAuth>
              <ResultsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/admin/questions"
          element={
            <RequireAdmin>
              <QuestionList />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/questions/new"
          element={
            <RequireAdmin>
              <QuestionEditor />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin/questions/:id/edit"
          element={
            <RequireAdmin>
              <QuestionEditor />
            </RequireAdmin>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
