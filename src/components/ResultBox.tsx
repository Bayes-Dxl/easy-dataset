import { CheckCircle2, XCircle } from "lucide-react";

export function ResultBox({
  success,
  message,
}: {
  success: boolean;
  message: string;
}) {
  return (
    <div
      className="rounded-md p-4 flex items-start gap-3"
      style={{
        background: success
          ? "hsl(142 71% 45% / 0.1)"
          : "hsl(0 84% 60% / 0.1)",
        border: `1px solid ${success ? "hsl(142 71% 45% / 0.3)" : "hsl(0 84% 60% / 0.3)"}`,
      }}
    >
      {success ? (
        <CheckCircle2
          className="w-5 h-5 flex-shrink-0 mt-0.5"
          style={{ color: "hsl(var(--success))" }}
        />
      ) : (
        <XCircle
          className="w-5 h-5 flex-shrink-0 mt-0.5"
          style={{ color: "hsl(var(--destructive))" }}
        />
      )}
      <span
        className="text-sm"
        style={{
          color: success
            ? "hsl(var(--success))"
            : "hsl(var(--destructive))",
        }}
      >
        {message}
      </span>
    </div>
  );
}
