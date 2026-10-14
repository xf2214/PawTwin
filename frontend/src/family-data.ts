import { useEffect, useState } from "react";
import { ApiError, request } from "./api";
import type { Measurement, Memory, Report } from "./family-api";

export type FamilyResource<T> = { data: T[]; status: "loading" | "ready" | "error"; retry: () => void };

function useResource<T>(scope: string, path: string, group: string, revision: number, version: number, unauthorized: (status: number) => void): FamilyResource<T> {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{ scope: string; data: T[]; status: "loading" | "ready" | "error" }>({ scope: "", data: [], status: "loading" });
  useEffect(() => {
    if (!scope) return;
    let active = true;
    const controller = new AbortController();
    setResult(previous => ({ scope, data: previous.scope === scope ? previous.data : [], status: "loading" }));
    request<Record<string, T[]>>(path, { signal: controller.signal }).then(value => {
      if (active) setResult({ scope, data: value[group], status: "ready" });
    }).catch(error => {
      if (!active) return;
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        setResult({ scope, data: [], status: "error" });
        unauthorized(error.status);
        return;
      }
      setResult(previous => ({ scope, data: previous.scope === scope ? previous.data : [], status: "error" }));
    });
    return () => { active = false; controller.abort(); };
  }, [scope, path, group, revision, version, attempt, unauthorized]);
  const visible = result.scope === scope ? result : { data: [], status: "loading" as const };
  return { ...visible, retry: () => setAttempt(value => value + 1) };
}

export function useFamilyData(householdId: string | undefined, petId: string | undefined, revision: number, version: number, unauthorized: (status: number) => void) {
  const scope = householdId && petId ? `${householdId}:${petId}` : "";
  const base = `/api/family/pets/${petId}`;
  return {
    measurements: useResource<Measurement>(scope, `${base}/measurements`, "records", revision, version, unauthorized),
    reports: useResource<Report>(scope, `${base}/reports`, "reports", revision, version, unauthorized),
    memories: useResource<Memory>(scope, `${base}/memories`, "memories", revision, version, unauthorized),
  };
}
