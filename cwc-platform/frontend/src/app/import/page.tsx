"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { importsApi, ImportJob } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Upload, Undo2, CheckCircle2, AlertTriangle } from "lucide-react";

const CWC_FIELDS = [
  { value: "", label: "— not imported —" },
  { value: "full_name", label: "Full name (auto-split)" },
  { value: "first_name", label: "First name" },
  { value: "last_name", label: "Last name" },
  { value: "email", label: "Email" },
  { value: "phone", label: "Phone" },
  { value: "organization_name", label: "Company / Organization" },
  { value: "notes", label: "Notes" },
];

const OUTCOME_BADGES: Record<string, { label: string; className: string }> = {
  create: { label: "Will create", className: "bg-success/15 text-success" },
  skip_duplicate: { label: "Duplicate — skip", className: "bg-muted text-muted-foreground" },
  update_existing: { label: "Will update", className: "bg-primary/15 text-primary" },
  error: { label: "Error", className: "bg-destructive/15 text-destructive" },
};

type Step = "upload" | "map" | "preview" | "done";

export default function ImportPage() {
  const { token } = useAuth();
  const [step, setStep] = useState<Step>("upload");
  const [csvText, setCsvText] = useState("");
  const [fileName, setFileName] = useState("");
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [detectedPreset, setDetectedPreset] = useState<string | null>(null);
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof importsApi.preview>> | null>(null);
  const [dedupeStrategy, setDedupeStrategy] = useState("skip");
  const [job, setJob] = useState<ImportJob | null>(null);
  const [history, setHistory] = useState<ImportJob[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadHistory = async () => {
    if (!token) return;
    try {
      setHistory(await importsApi.history(token));
    } catch {
      // history is non-critical; the wizard still works without it
    }
  };

  const handleFile = async (file: File) => {
    setError("");
    const text = await file.text();
    const firstLine = text.split(/\r?\n/, 1)[0] || "";
    setCsvText(text);
    setFileName(file.name);
    setHeaders(firstLine.split(",").map((h) => h.trim().replace(/^"|"$/g, "")));
    if (!token) return;
    setLoading(true);
    try {
      // Let the backend try preset detection first
      const result = await importsApi.preview(token, {
        entity_type: "contacts",
        csv_text: text,
        dedupe_strategy: dedupeStrategy,
      });
      setDetectedPreset(result.preset);
      setMapping(result.mapping);
      setPreview(result);
      setStep("map");
    } catch {
      // No preset detected — start with an empty mapping for manual mapping
      setDetectedPreset(null);
      setMapping({});
      setPreview(null);
      setStep("map");
    } finally {
      setLoading(false);
    }
  };

  const runPreview = async () => {
    if (!token) return;
    setError("");
    setLoading(true);
    try {
      const result = await importsApi.preview(token, {
        entity_type: "contacts",
        csv_text: csvText,
        mapping,
        dedupe_strategy: dedupeStrategy,
      });
      setPreview(result);
      setStep("preview");
    } catch (err: any) {
      setError(err.message || "Preview failed");
    } finally {
      setLoading(false);
    }
  };

  const runCommit = async () => {
    if (!token) return;
    setError("");
    setLoading(true);
    try {
      const committed = await importsApi.commit(token, {
        entity_type: "contacts",
        csv_text: csvText,
        mapping,
        dedupe_strategy: dedupeStrategy,
      });
      setJob(committed);
      setStep("done");
      loadHistory();
    } catch (err: any) {
      setError(err.message || "Import failed");
    } finally {
      setLoading(false);
    }
  };

  const runUndo = async (jobId: string) => {
    if (!token) return;
    setError("");
    try {
      await importsApi.undo(token, jobId);
      loadHistory();
      if (job?.id === jobId) setJob({ ...job, status: "undone" });
    } catch (err: any) {
      setError(err.message || "Undo failed");
    }
  };

  const reset = () => {
    setStep("upload");
    setCsvText("");
    setFileName("");
    setHeaders([]);
    setMapping({});
    setDetectedPreset(null);
    setPreview(null);
    setJob(null);
    setError("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Import Data</h1>
        <p className="text-muted-foreground">
          Bring contacts over from HoneyBook, Dubsado, or any CSV — preview first, undo anytime.
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" aria-hidden />
          {error}
        </div>
      )}

      {step === "upload" && (
        <Card>
          <CardHeader>
            <CardTitle>1. Upload your export file</CardTitle>
            <CardDescription>
              Export contacts from your old platform as CSV, then drop the file here.
              HoneyBook and Dubsado exports are recognized automatically.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <label className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 cursor-pointer hover:border-primary/50">
              <Upload className="h-8 w-8 text-muted-foreground" aria-hidden />
              <span className="text-sm text-muted-foreground">
                {loading ? "Reading file..." : "Click to choose a .csv file"}
              </span>
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </label>
          </CardContent>
        </Card>
      )}

      {step === "map" && (
        <Card>
          <CardHeader>
            <CardTitle>2. Map columns</CardTitle>
            <CardDescription>
              {detectedPreset
                ? `Recognized a ${detectedPreset} export (${fileName}) — mapping pre-filled, adjust if needed.`
                : `We couldn't recognize ${fileName} — tell us what each column is.`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>CSV column</TableHead>
                    <TableHead>Imports into</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {headers.map((header) => (
                    <TableRow key={header}>
                      <TableCell className="font-medium">{header}</TableCell>
                      <TableCell>
                        <Select
                          value={mapping[header] || ""}
                          onValueChange={(value) =>
                            setMapping((m) => {
                              const next = { ...m };
                              if (value) next[header] = value;
                              else delete next[header];
                              return next;
                            })
                          }
                        >
                          <SelectTrigger className="w-64">
                            <SelectValue placeholder="— not imported —" />
                          </SelectTrigger>
                          <SelectContent>
                            {CWC_FIELDS.filter((f) => f.value !== "").map((f) => (
                              <SelectItem key={f.value} value={f.value}>
                                {f.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">If a contact already exists:</span>
              <Select value={dedupeStrategy} onValueChange={setDedupeStrategy}>
                <SelectTrigger className="w-56">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="skip">Skip it</SelectItem>
                  <SelectItem value="update">Fill in blank fields only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button onClick={runPreview} disabled={loading}>
                {loading ? "Checking..." : "Preview import"}
              </Button>
              <Button variant="outline" onClick={reset}>Start over</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === "preview" && preview && (
        <Card>
          <CardHeader>
            <CardTitle>3. Preview — nothing imported yet</CardTitle>
            <CardDescription>
              {preview.counts.create} to create · {preview.counts.skip_duplicate} duplicates skipped ·{" "}
              {preview.counts.update_existing} to update · {preview.counts.error} errors
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Row</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Outcome</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {preview.rows.map((row) => {
                    const badge = OUTCOME_BADGES[row.outcome] || OUTCOME_BADGES.error;
                    return (
                      <TableRow key={row.row_index}>
                        <TableCell>{row.row_index + 1}</TableCell>
                        <TableCell>
                          {[row.data.first_name, row.data.last_name].filter(Boolean).join(" ") || "—"}
                        </TableCell>
                        <TableCell>{row.data.email || "—"}</TableCell>
                        <TableCell>
                          <Badge className={badge.className} variant="outline">
                            {badge.label}
                          </Badge>
                          {row.error && (
                            <span className="ml-2 text-sm text-destructive">{row.error}</span>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <div className="flex gap-2">
              <Button onClick={runCommit} disabled={loading || preview.counts.create + preview.counts.update_existing === 0}>
                {loading
                  ? "Importing..."
                  : `Import ${preview.counts.create + preview.counts.update_existing} contacts`}
              </Button>
              <Button variant="outline" onClick={() => setStep("map")}>Back to mapping</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === "done" && job && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-success" aria-hidden />
              Import complete
            </CardTitle>
            <CardDescription>
              {job.created_count} created · {job.updated_count} updated · {job.skipped_count} skipped ·{" "}
              {job.error_count} errors
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            {job.status === "committed" ? (
              <Button variant="outline" onClick={() => runUndo(job.id)}>
                <Undo2 className="h-4 w-4 mr-2" aria-hidden />
                Undo this import
              </Button>
            ) : (
              <Badge variant="outline">Undone</Badge>
            )}
            <Button onClick={reset}>Import another file</Button>
          </CardContent>
        </Card>
      )}

      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Import history</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((h) => (
                  <TableRow key={h.id}>
                    <TableCell>
                      {h.created_at ? new Date(h.created_at).toLocaleString() : "—"}
                    </TableCell>
                    <TableCell className="capitalize">{h.source}</TableCell>
                    <TableCell>{h.created_count}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{h.status}</Badge>
                    </TableCell>
                    <TableCell>
                      {h.status === "committed" && h.created_count > 0 && (
                        <Button size="sm" variant="ghost" onClick={() => runUndo(h.id)}>
                          <Undo2 className="h-4 w-4 mr-1" aria-hidden />
                          Undo
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
