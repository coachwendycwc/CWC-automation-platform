"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { availabilityApi } from "@/lib/api";
import { WeeklyAvailability, AvailabilityOverride } from "@/types";
import { Plus, Trash2, ArrowLeft, Calendar } from "lucide-react";
import Link from "next/link";

const DAYS = [
  { key: "monday", label: "Monday", index: 0 },
  { key: "tuesday", label: "Tuesday", index: 1 },
  { key: "wednesday", label: "Wednesday", index: 2 },
  { key: "thursday", label: "Thursday", index: 3 },
  { key: "friday", label: "Friday", index: 4 },
  { key: "saturday", label: "Saturday", index: 5 },
  { key: "sunday", label: "Sunday", index: 6 },
] as const;

type DayKey = typeof DAYS[number]["key"];

interface TimeSlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export default function AvailabilityPage() {
  const [weekly, setWeekly] = useState<Record<DayKey, TimeSlot[]>>({
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: [],
    sunday: [],
  });
  const [overrides, setOverrides] = useState<AvailabilityOverride[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [overrideForm, setOverrideForm] = useState({
    date: "",
    is_available: false,
    start_time: "",
    end_time: "",
    reason: "",
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const [weeklyResponse, overridesResponse] = await Promise.all([
        availabilityApi.getWeekly(token),
        availabilityApi.listOverrides(token),
      ]);

      // Convert response to our format
      const newWeekly: Record<DayKey, TimeSlot[]> = {
        monday: [],
        tuesday: [],
        wednesday: [],
        thursday: [],
        friday: [],
        saturday: [],
        sunday: [],
      };

      DAYS.forEach(({ key }) => {
        const slots = weeklyResponse[key] || [];
        newWeekly[key] = slots.map((s: any) => ({
          day_of_week: s.day_of_week,
          start_time: s.start_time,
          end_time: s.end_time,
          is_active: s.is_active,
        }));
      });

      setWeekly(newWeekly);
      setOverrides(overridesResponse.items || []);
    } catch (err) {
      console.error("Failed to load availability:", err);
    } finally {
      setLoading(false);
    }
  };

  const addTimeSlot = (dayKey: DayKey, dayIndex: number) => {
    setWeekly({
      ...weekly,
      [dayKey]: [
        ...weekly[dayKey],
        { day_of_week: dayIndex, start_time: "09:00", end_time: "17:00", is_active: true },
      ],
    });
  };

  const removeTimeSlot = (dayKey: DayKey, index: number) => {
    setWeekly({
      ...weekly,
      [dayKey]: weekly[dayKey].filter((_, i) => i !== index),
    });
  };

  const updateTimeSlot = (dayKey: DayKey, index: number, field: string, value: string) => {
    setWeekly({
      ...weekly,
      [dayKey]: weekly[dayKey].map((slot, i) =>
        i === index ? { ...slot, [field]: value } : slot
      ),
    });
  };

  const saveWeekly = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      // Flatten all time slots
      const allSlots: TimeSlot[] = [];
      DAYS.forEach(({ key }) => {
        weekly[key].forEach((slot) => {
          allSlots.push(slot);
        });
      });

      await availabilityApi.updateWeekly(token, { availabilities: allSlots });
      alert("Availability saved!");
    } catch (err: any) {
      alert(err.message || "Failed to save availability");
    } finally {
      setSaving(false);
    }
  };

  const addOverride = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await availabilityApi.createOverride(token, {
        date: overrideForm.date,
        is_available: overrideForm.is_available,
        start_time: overrideForm.is_available ? overrideForm.start_time || null : null,
        end_time: overrideForm.is_available ? overrideForm.end_time || null : null,
        reason: overrideForm.reason || null,
      });

      setShowOverrideForm(false);
      setOverrideForm({ date: "", is_available: false, start_time: "", end_time: "", reason: "" });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to add override");
    }
  };

  const deleteOverride = async (id: string) => {
    if (!confirm("Delete this date override?")) return;
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await availabilityApi.deleteOverride(token, id);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to delete override");
    }
  };

  if (loading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/settings" className="text-gray-500 hover:text-gray-700">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Availability</h1>
            <p className="text-gray-600">Set your weekly schedule and date-specific overrides</p>
          </div>
        </div>

        {/* Weekly Schedule */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Schedule</CardTitle>
            <CardDescription>Set your recurring availability for each day of the week</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {DAYS.map(({ key, label, index }) => (
              <div key={key} className="flex items-start gap-4 py-3 border-b border-gray-100 last:border-0">
                <div className="w-28 pt-2 font-medium text-gray-700">{label}</div>
                <div className="flex-1 space-y-2">
                  {weekly[key].length === 0 ? (
                    <p className="text-sm text-gray-400 py-2">Not available</p>
                  ) : (
                    weekly[key].map((slot, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <Input
                          type="time"
                          value={slot.start_time}
                          onChange={(e) => updateTimeSlot(key, i, "start_time", e.target.value)}
                          className="w-32"
                        />
                        <span className="text-gray-500">to</span>
                        <Input
                          type="time"
                          value={slot.end_time}
                          onChange={(e) => updateTimeSlot(key, i, "end_time", e.target.value)}
                          className="w-32"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTimeSlot(key, i)}
                          className="text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => addTimeSlot(key, index)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add time slot
                  </Button>
                </div>
              </div>
            ))}

            <div className="pt-4">
              <Button onClick={saveWeekly} disabled={saving}>
                {saving ? "Saving..." : "Save Weekly Schedule"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Date Overrides */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Date Overrides</CardTitle>
              <CardDescription>Block specific dates or add extra availability</CardDescription>
            </div>
            {!showOverrideForm && (
              <Button onClick={() => setShowOverrideForm(true)} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Override
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {showOverrideForm && (
              <div className="mb-6 p-4 border border-gray-200 rounded-lg space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                    <Input
                      type="date"
                      value={overrideForm.date}
                      onChange={(e) => setOverrideForm({ ...overrideForm, date: e.target.value })}
                      min={new Date().toISOString().split("T")[0]}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      value={overrideForm.is_available ? "available" : "blocked"}
                      onChange={(e) =>
                        setOverrideForm({ ...overrideForm, is_available: e.target.value === "available" })
                      }
                    >
                      <option value="blocked">Blocked (Day off)</option>
                      <option value="available">Available (Extra hours)</option>
                    </select>
                  </div>
                </div>

                {overrideForm.is_available && (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                      <Input
                        type="time"
                        value={overrideForm.start_time}
                        onChange={(e) => setOverrideForm({ ...overrideForm, start_time: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                      <Input
                        type="time"
                        value={overrideForm.end_time}
                        onChange={(e) => setOverrideForm({ ...overrideForm, end_time: e.target.value })}
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reason (optional)</label>
                  <Input
                    value={overrideForm.reason}
                    onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })}
                    placeholder="Vacation, Conference, etc."
                  />
                </div>

                <div className="flex gap-3">
                  <Button onClick={addOverride}>Add Override</Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowOverrideForm(false);
                      setOverrideForm({ date: "", is_available: false, start_time: "", end_time: "", reason: "" });
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {overrides.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No date overrides set</p>
            ) : (
              <div className="space-y-2">
                {overrides.map((override) => (
                  <div
                    key={override.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-gray-400" />
                      <div>
                        <div className="font-medium">
                          {new Date(override.date + "T00:00:00").toLocaleDateString("en-US", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </div>
                        <div className="text-sm text-gray-500">
                          {override.is_available ? (
                            <>Available: {override.start_time} - {override.end_time}</>
                          ) : (
                            <span className="text-red-600">Blocked</span>
                          )}
                          {override.reason && ` - ${override.reason}`}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteOverride(override.id)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
