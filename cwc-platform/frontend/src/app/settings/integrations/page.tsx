"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Calendar, Link2, RefreshCw, Star, Trash2 } from "lucide-react";

import { Shell } from "@/components/layout/Shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { integrationsApi } from "@/lib/api";
import type { CalendarConnection, IntegrationStatus } from "@/types";

export default function IntegrationsSettingsPage() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [connections, setConnections] = useState<CalendarConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleConnected = params.get("google_connected");
    const googleError = params.get("google_error");
    const zoomConnected = params.get("zoom_connected");
    const zoomError = params.get("zoom_error");

    if (googleConnected === "true") {
      setMessage("Google Calendar connected successfully.");
    }
    if (googleError) {
      setError(`Google Calendar connection failed: ${googleError}`);
    }
    if (zoomConnected === "true") {
      setMessage("Zoom connected successfully.");
    }
    if (zoomError) {
      setError(`Zoom connection failed: ${zoomError}`);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("You must be signed in to manage integrations.");
        return;
      }

      const [statusResponse, connectionsResponse] = await Promise.all([
        integrationsApi.getStatus(token),
        integrationsApi.listCalendarConnections(token),
      ]);

      setStatus(statusResponse);
      setConnections(connectionsResponse);
    } catch (err: any) {
      setError(err.message || "Failed to load integrations");
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGoogle = async () => {
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await integrationsApi.getGoogleAuthUrl(token);
      window.location.href = response.auth_url;
    } catch (err: any) {
      setError(err.message || "Failed to start Google Calendar connection");
    }
  };

  const handleSetPrimary = async (connectionId: string) => {
    setActionLoadingId(connectionId);
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await integrationsApi.setPrimaryCalendarConnection(token, connectionId);
      setMessage("Primary calendar updated.");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to set primary calendar");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleConnectZoom = async () => {
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await integrationsApi.getZoomAuthUrl(token);
      window.location.href = response.auth_url;
    } catch (err: any) {
      setError(err.message || "Failed to start Zoom connection");
    }
  };

  const handleDisconnectGoogle = async () => {
    if (!confirm("Disconnect Google Calendar and Google Meet?")) return;

    setActionLoadingId("google");
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await integrationsApi.disconnectGoogle(token);
      setMessage("Google Calendar disconnected.");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to disconnect Google Calendar");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDisconnectZoom = async () => {
    if (!confirm("Disconnect Zoom?")) return;

    setActionLoadingId("zoom");
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await integrationsApi.disconnectZoom(token);
      setMessage("Zoom disconnected.");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to disconnect Zoom");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDisconnectConnection = async (connectionId: string) => {
    if (!confirm("Disconnect this calendar connection?")) return;

    setActionLoadingId(connectionId);
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await integrationsApi.disconnectCalendarConnection(token, connectionId);
      setMessage("Calendar connection disconnected.");
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to disconnect calendar");
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/settings" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Integrations</h1>
            <p className="text-muted-foreground">
              Connect calendars and choose the account that receives bookings.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {message && (
          <div className="rounded-md border border-primary/20 bg-primary/10 px-4 py-3 text-sm text-primary">
            {message}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardHeader>
              <CardTitle>Connected Calendars</CardTitle>
              <CardDescription>
                These calendar accounts are used for availability, conflict checking, and booking write-back.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <>
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </>
              ) : connections.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                  No calendar connections yet. Connect Google Calendar to start building a unified availability and Google Meet workflow.
                </div>
              ) : (
                connections.map((connection) => (
                  <div
                    key={connection.id}
                    className="flex items-start justify-between gap-4 rounded-lg border border-border p-4"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="font-medium text-foreground">
                          {connection.account_email || connection.calendar_name || connection.calendar_id}
                        </div>
                        <Badge variant="outline">{connection.provider}</Badge>
                        {connection.is_primary && <Badge>Primary</Badge>}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Calendar: {connection.calendar_name || connection.calendar_id}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Sync: {connection.sync_direction.replace("_", " ")}
                        {" • "}
                        Conflict checks: {connection.conflict_check_enabled ? "On" : "Off"}
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      {!connection.is_primary && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => void handleSetPrimary(connection.id)}
                          disabled={actionLoadingId === connection.id}
                        >
                          <Star className="mr-2 h-4 w-4" />
                          {actionLoadingId === connection.id ? "Saving..." : "Set Primary"}
                        </Button>
                      )}

                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => void handleDisconnectConnection(connection.id)}
                        disabled={actionLoadingId === connection.id}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Disconnect
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Connection Status</CardTitle>
                <CardDescription>Current external integrations for scheduling and meetings.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading ? (
                  <>
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                  </>
                ) : (
                  <>
                    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Calendar className="h-5 w-5 text-primary" />
                        <div>
                          <div className="font-medium text-foreground">Google Calendar + Meet</div>
                          <div className="text-sm text-muted-foreground">
                            {status?.google_calendar_accounts || 0} connected account(s)
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={status?.google_calendar ? "default" : "secondary"}>
                          {status?.google_calendar ? "Connected" : "Not Connected"}
                        </Badge>
                        {status?.google_calendar && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void handleDisconnectGoogle()}
                            disabled={actionLoadingId === "google"}
                          >
                            {actionLoadingId === "google" ? "Disconnecting..." : "Disconnect"}
                          </Button>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Link2 className="h-5 w-5 text-primary" />
                        <div>
                          <div className="font-medium text-foreground">Zoom</div>
                          <div className="text-sm text-muted-foreground">
                            Meeting provider for Zoom-based booking types
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={status?.zoom ? "default" : "secondary"}>
                          {status?.zoom ? "Connected" : "Not Connected"}
                        </Badge>
                        {status?.zoom && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void handleDisconnectZoom()}
                            disabled={actionLoadingId === "zoom"}
                          >
                            {actionLoadingId === "zoom" ? "Disconnecting..." : "Disconnect"}
                          </Button>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Add Connection</CardTitle>
                <CardDescription>
                  Connect the tools Wendy already uses so availability and meeting links come from one place.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" onClick={() => void handleConnectGoogle()}>
                  <Calendar className="mr-2 h-4 w-4" />
                  Connect Google Calendar + Meet
                </Button>

                <Button variant="outline" className="w-full" onClick={() => void handleConnectZoom()}>
                  <Link2 className="mr-2 h-4 w-4" />
                  Connect Zoom
                </Button>

                <Button variant="outline" className="w-full" disabled>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Microsoft Calendar (Next)
                </Button>

                <p className="text-sm text-muted-foreground">
                  Google powers calendar sync and Google Meet. Zoom can be connected separately for Zoom-based booking
                  types. Microsoft and other providers are planned next.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Shell>
  );
}
