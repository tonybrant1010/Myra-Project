export type ScaleKey = "a" | "p" | "h" | "c";
export type MeasurementNorms = Partial<Record<ScaleKey, number>> & { source?: string };

export function hasMeasuredNorms(norms: MeasurementNorms | null | undefined): boolean {
  return !!norms && norms.source !== "manual_code" &&
    (["a", "p", "h", "c"] as const).every((key) =>
      typeof norms[key] === "number" && Number.isFinite(norms[key]));
}
