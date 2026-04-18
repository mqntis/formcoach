import { useEffect, useState } from "react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { Session } from "../types";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    api.get<{ sessions: Session[] }>("/api/sessions/").then(({ data }) => {
      setSessions(data.sessions);
    });
  }, []);

  return (
    <main>
      <h2>Dashboard</h2>
      <p>Welcome, {user?.email}</p>
      <button onClick={logout}>Logout</button>
      <h3>Your Sessions</h3>
      {sessions.length === 0 ? (
        <p>No sessions yet. Create your first one!</p>
      ) : (
        <ul>
          {sessions.map((s) => (
            <li key={s.id}>{s.title}</li>
          ))}
        </ul>
      )}
    </main>
  );
}
