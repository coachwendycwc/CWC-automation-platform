"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { mileageApi, contactsApi } from "@/lib/api";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Plus, Car, Pencil, Trash2, ArrowLeft, MapPin } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

interface MileageLog {
  id: string;
  trip_date: string;
  description: string;
  purpose: string;
  miles: number;
  rate_per_mile: number;
  total_deduction: number;
  start_location: string | null;
  end_location: string | null;
  round_trip: boolean;
  contact_id: string | null;
  tax_year: number;
  notes: string | null;
}

interface Contact {
  id: string;
  first_name: string;
  last_name: string;
}

const PURPOSE_OPTIONS = [
  { value: "client_meeting", label: "Client Meeting" },
  { value: "business_errand", label: "Business Errand" },
  { value: "conference", label: "Conference/Event" },
  { value: "networking", label: "Networking" },
  { value: "training", label: "Training/Education" },
  { value: "other", label: "Other Business" },
];

export default function MileagePage() {
  const { token } = useAuth();
  const currentYear = new Date().getFullYear();
  const [logs, setLogs] = useState<MileageLog[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [taxYear, setTaxYear] = useState(currentYear);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLog, setEditingLog] = useState<MileageLog | null>(null);
  const [summary, setSummary] = useState({ total_miles: 0, total_deduction: 0, trip_count: 0 });

  // Form state
  const [formData, setFormData] = useState({
    trip_date: new Date().toISOString().split("T")[0],
    description: "",
    purpose: "client_meeting",
    miles: "",
    start_location: "",
    end_location: "",
    round_trip: false,
    contact_id: "",
    notes: "",
  });

  useEffect(() => {
    if (token) {
      loadContacts();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      loadMileage();
      loadSummary();
    }
  }, [token, taxYear]);

  const loadContacts = async () => {
    if (!token) return;
    try {
      const data = await contactsApi.list(token, { size: 100 });
      setContacts(data.items || []);
    } catch (error) {
      console.error("Failed to load contacts:", error);
    }
  };

  const loadMileage = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await mileageApi.list(token, { tax_year: taxYear });
      setLogs(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to load mileage logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    if (!token) return;
    try {
      const data = await mileageApi.getSummary(token, taxYear);
      setSummary(data);
    } catch (error) {
      console.error("Failed to load summary:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const data = {
        ...formData,
        miles: parseFloat(formData.miles),
        contact_id: formData.contact_id || null,
      };

      if (editingLog) {
        await mileageApi.update(token, editingLog.id, data);
        toast.success("Mileage log updated");
      } else {
        await mileageApi.create(token, data);
        toast.success("Mileage logged");
      }

      setDialogOpen(false);
      resetForm();
      loadMileage();
      loadSummary();
    } catch (error) {
      toast.error("Failed to save mileage");
    }
  };

  const handleEdit = (log: MileageLog) => {
    setEditingLog(log);
    setFormData({
      trip_date: log.trip_date,
      description: log.description,
      purpose: log.purpose,
      miles: log.miles.toString(),
      start_location: log.start_location || "",
      end_location: log.end_location || "",
      round_trip: log.round_trip,
      contact_id: log.contact_id || "",
      notes: log.notes || "",
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!token || !confirm("Are you sure you want to delete this mileage log?")) return;
    try {
      await mileageApi.delete(token, id);
      toast.success("Mileage log deleted");
      loadMileage();
      loadSummary();
    } catch (error) {
      toast.error("Failed to delete mileage log");
    }
  };

  const resetForm = () => {
    setEditingLog(null);
    setFormData({
      trip_date: new Date().toISOString().split("T")[0],
      description: "",
      purpose: "client_meeting",
      miles: "",
      start_location: "",
      end_location: "",
      round_trip: false,
      contact_id: "",
      notes: "",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const getPurposeLabel = (value: string) => {
    return PURPOSE_OPTIONS.find((p) => p.value === value)?.label || value;
  };

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <Shell>
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/bookkeeping">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Mileage Tracking</h1>
          <p className="text-muted-foreground">Log business trips for IRS mileage deductions</p>
        </div>
        <Select value={taxYear.toString()} onValueChange={(v) => setTaxYear(parseInt(v))}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {years.map((year) => (
              <SelectItem key={year} value={year.toString()}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Log Trip
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>{editingLog ? "Edit Trip" : "Log Business Trip"}</DialogTitle>
                <DialogDescription>
                  Record mileage for tax deduction purposes
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="trip_date">Trip Date *</Label>
                    <Input
                      id="trip_date"
                      type="date"
                      value={formData.trip_date}
                      onChange={(e) => setFormData({ ...formData, trip_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="purpose">Purpose *</Label>
                    <Select
                      value={formData.purpose}
                      onValueChange={(v) => setFormData({ ...formData, purpose: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PURPOSE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description *</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="e.g., Meeting with client at downtown office"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="start_location">From</Label>
                    <Input
                      id="start_location"
                      value={formData.start_location}
                      onChange={(e) => setFormData({ ...formData, start_location: e.target.value })}
                      placeholder="Starting location"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="end_location">To</Label>
                    <Input
                      id="end_location"
                      value={formData.end_location}
                      onChange={(e) => setFormData({ ...formData, end_location: e.target.value })}
                      placeholder="Destination"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="miles">Miles (one way) *</Label>
                    <Input
                      id="miles"
                      type="number"
                      step="0.1"
                      value={formData.miles}
                      onChange={(e) => setFormData({ ...formData, miles: e.target.value })}
                      placeholder="0.0"
                      required
                    />
                  </div>
                  <div className="flex items-end pb-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="round_trip"
                        checked={formData.round_trip}
                        onCheckedChange={(checked) => setFormData({ ...formData, round_trip: checked as boolean })}
                      />
                      <Label htmlFor="round_trip">Round trip (double miles)</Label>
                    </div>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="contact">Related Client (optional)</Label>
                  <Select
                    value={formData.contact_id}
                    onValueChange={(v) => setFormData({ ...formData, contact_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select client" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {contacts.map((contact) => (
                        <SelectItem key={contact.id} value={contact.id}>
                          {contact.first_name} {contact.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Additional details for your records..."
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">{editingLog ? "Update" : "Log"} Trip</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Miles</CardTitle>
            <Car className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_miles.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{summary.trip_count} trips logged</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tax Deduction</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(summary.total_deduction)}
            </div>
            <p className="text-xs text-muted-foreground">At IRS standard rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Per Trip</CardTitle>
            <Car className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.trip_count > 0 ? (summary.total_miles / summary.trip_count).toFixed(1) : 0} mi
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.trip_count > 0 ? formatCurrency(summary.total_deduction / summary.trip_count) : "$0"} deduction
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Mileage Table */}
      <Card>
        <CardHeader>
          <CardTitle>Trip Log ({total})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8">
              <Car className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No trips logged yet</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Log Your First Trip
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Purpose</TableHead>
                  <TableHead>Route</TableHead>
                  <TableHead className="text-right">Miles</TableHead>
                  <TableHead className="text-right">Deduction</TableHead>
                  <TableHead className="w-20"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      {new Date(log.trip_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="font-medium">{log.description}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{getPurposeLabel(log.purpose)}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {log.start_location && log.end_location ? (
                        <>
                          {log.start_location} → {log.end_location}
                          {log.round_trip && " (RT)"}
                        </>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-right">{log.miles}</TableCell>
                    <TableCell className="text-right font-medium text-green-600">
                      {formatCurrency(log.total_deduction)}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(log)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(log.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
    </Shell>
  );
}
