"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Shell } from "@/components/layout/Shell";
import {
  icfTrackerApi,
  CoachingSession,
  ICFSummary,
  ClientHoursSummary,
  CoachingSessionCreate,
  ICFCertificationDashboard,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Clock,
  Users,
  DollarSign,
  Heart,
  User,
  Plus,
  Download,
  Search,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Trash2,
  Pencil,
  Upload,
  Link,
  Award,
  GraduationCap,
  BookOpen,
  FileCheck,
  Target,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

export default function ICFTrackerPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<ICFSummary | null>(null);
  const [clientSummary, setClientSummary] = useState<ClientHoursSummary[]>([]);
  const [sessions, setSessions] = useState<CoachingSession[]>([]);
  const [certDashboard, setCertDashboard] = useState<ICFCertificationDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"summary" | "clients" | "sessions" | "journey">("summary");

  // Filters
  const [search, setSearch] = useState("");
  const [sessionType, setSessionType] = useState<string>("");
  const [paymentType, setPaymentType] = useState<string>("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Dialog
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editSession, setEditSession] = useState<CoachingSession | null>(null);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [progressFormData, setProgressFormData] = useState({
    acc_training_hours: 0,
    acc_training_provider: "",
    acc_mentor_hours: 0,
    acc_mentor_individual_hours: 0,
    acc_mentor_group_hours: 0,
    acc_mentor_name: "",
    acc_exam_passed: false,
    pcc_training_hours: 0,
    pcc_training_provider: "",
    pcc_mentor_hours: 0,
    pcc_mentor_individual_hours: 0,
    pcc_mentor_group_hours: 0,
    pcc_mentor_name: "",
    pcc_exam_passed: false,
    mcc_training_hours: 0,
    mcc_training_provider: "",
    mcc_mentor_hours: 0,
    mcc_mentor_individual_hours: 0,
    mcc_mentor_group_hours: 0,
    mcc_mentor_name: "",
    mcc_exam_passed: false,
  });
  const [formData, setFormData] = useState<CoachingSessionCreate>({
    client_name: "",
    session_date: new Date().toISOString().split("T")[0],
    duration_hours: 1,
    session_type: "individual",
    payment_type: "paid",
  });

  useEffect(() => {
    if (token) {
      loadData();
    }
  }, [token, view, page, search, sessionType, paymentType]);

  const loadData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      // Always load summary and certification dashboard
      const [summaryData, certData] = await Promise.all([
        icfTrackerApi.getSummary(token),
        icfTrackerApi.getCertificationDashboard(token),
      ]);
      setSummary(summaryData);
      setCertDashboard(certData);

      if (view === "clients") {
        const clientData = await icfTrackerApi.getByClient(token);
        setClientSummary(clientData);
      } else if (view === "sessions") {
        const result = await icfTrackerApi.list(token, {
          page,
          size: 50,
          client_name: search || undefined,
          session_type: sessionType || undefined,
          payment_type: paymentType || undefined,
        });
        setSessions(result.items);
        setTotal(result.total);
      }
    } catch (error) {
      console.error("Failed to load ICF data:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!token) return;
    const url = icfTrackerApi.exportCSV(token);
    window.open(url, "_blank");
  };

  const handleAddSession = async () => {
    if (!token) return;
    try {
      await icfTrackerApi.create(token, formData);
      toast.success("Session added");
      setShowAddDialog(false);
      resetForm();
      loadData();
    } catch (error) {
      console.error("Failed to add session:", error);
      toast.error("Failed to add session");
    }
  };

  const handleUpdateSession = async () => {
    if (!token || !editSession) return;
    try {
      await icfTrackerApi.update(token, editSession.id, formData);
      toast.success("Session updated");
      setEditSession(null);
      resetForm();
      loadData();
    } catch (error) {
      console.error("Failed to update session:", error);
      toast.error("Failed to update session");
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!token) return;
    if (!confirm("Delete this session?")) return;
    try {
      await icfTrackerApi.delete(token, id);
      toast.success("Session deleted");
      loadData();
    } catch (error) {
      console.error("Failed to delete session:", error);
      toast.error("Failed to delete session");
    }
  };

  const handleMatchContacts = async () => {
    if (!token) return;
    try {
      const result = await icfTrackerApi.matchContacts(token);
      toast.success(`Matched ${result.matched} sessions to contacts`);
      loadData();
    } catch (error) {
      console.error("Failed to match contacts:", error);
      toast.error("Failed to match contacts");
    }
  };

  const resetForm = () => {
    setFormData({
      client_name: "",
      session_date: new Date().toISOString().split("T")[0],
      duration_hours: 1,
      session_type: "individual",
      payment_type: "paid",
    });
  };

  const openProgressDialog = () => {
    if (certDashboard?.progress) {
      const p = certDashboard.progress;
      setProgressFormData({
        acc_training_hours: p.acc_training_hours || 0,
        acc_training_provider: p.acc_training_provider || "",
        acc_mentor_hours: p.acc_mentor_hours || 0,
        acc_mentor_individual_hours: p.acc_mentor_individual_hours || 0,
        acc_mentor_group_hours: p.acc_mentor_group_hours || 0,
        acc_mentor_name: p.acc_mentor_name || "",
        acc_exam_passed: p.acc_exam_passed || false,
        pcc_training_hours: p.pcc_training_hours || 0,
        pcc_training_provider: p.pcc_training_provider || "",
        pcc_mentor_hours: p.pcc_mentor_hours || 0,
        pcc_mentor_individual_hours: p.pcc_mentor_individual_hours || 0,
        pcc_mentor_group_hours: p.pcc_mentor_group_hours || 0,
        pcc_mentor_name: p.pcc_mentor_name || "",
        pcc_exam_passed: p.pcc_exam_passed || false,
        mcc_training_hours: p.mcc_training_hours || 0,
        mcc_training_provider: p.mcc_training_provider || "",
        mcc_mentor_hours: p.mcc_mentor_hours || 0,
        mcc_mentor_individual_hours: p.mcc_mentor_individual_hours || 0,
        mcc_mentor_group_hours: p.mcc_mentor_group_hours || 0,
        mcc_mentor_name: p.mcc_mentor_name || "",
        mcc_exam_passed: p.mcc_exam_passed || false,
      });
    }
    setShowProgressDialog(true);
  };

  const handleSaveProgress = async () => {
    if (!token) return;
    try {
      await icfTrackerApi.updateCertificationProgress(token, progressFormData);
      toast.success("Certification progress updated");
      setShowProgressDialog(false);
      loadData();
    } catch (error) {
      console.error("Failed to update progress:", error);
      toast.error("Failed to update progress");
    }
  };

  const openEditDialog = (session: CoachingSession) => {
    setEditSession(session);
    setFormData({
      client_name: session.client_name,
      client_email: session.client_email,
      session_date: session.session_date,
      duration_hours: session.duration_hours,
      session_type: session.session_type,
      group_size: session.group_size,
      payment_type: session.payment_type,
      meeting_title: session.meeting_title,
      notes: session.notes,
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">ICF Hours Tracker</h1>
            <p className="text-gray-500">
              Track coaching hours for ICF certification
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={openProgressDialog}>
              <Pencil className="h-4 w-4 mr-2" />
              Edit Progress
            </Button>
            <Button variant="outline" onClick={handleMatchContacts}>
              <Link className="h-4 w-4 mr-2" />
              Match Contacts
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Session
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-500">Total Hours</p>
                    <p className="text-2xl font-bold">{summary.total_hours}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-500">Individual</p>
                    <p className="text-2xl font-bold">{summary.individual_hours}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-500">Group</p>
                    <p className="text-2xl font-bold">{summary.group_hours}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                  <div>
                    <p className="text-sm text-gray-500">Paid</p>
                    <p className="text-2xl font-bold">{summary.paid_hours}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Heart className="h-5 w-5 text-pink-600" />
                  <div>
                    <p className="text-sm text-gray-500">Pro Bono</p>
                    <p className="text-2xl font-bold">{summary.pro_bono_hours}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-orange-600" />
                  <div>
                    <p className="text-sm text-gray-500">Clients</p>
                    <p className="text-2xl font-bold">{summary.total_clients}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* View Tabs */}
        <div className="flex gap-2">
          <Button
            variant={view === "journey" ? "default" : "outline"}
            onClick={() => setView("journey")}
          >
            🎯 Journey
          </Button>
          <Button
            variant={view === "summary" ? "default" : "outline"}
            onClick={() => setView("summary")}
          >
            Summary
          </Button>
          <Button
            variant={view === "clients" ? "default" : "outline"}
            onClick={() => setView("clients")}
          >
            By Client
          </Button>
          <Button
            variant={view === "sessions" ? "default" : "outline"}
            onClick={() => setView("sessions")}
          >
            All Sessions
          </Button>
        </div>

        {/* Journey View - Step-by-Step Certification Checklist */}
        {view === "journey" && certDashboard && (
          <div className="space-y-6">
            {/* What's Next Banner */}
            {(() => {
              const p = certDashboard.progress;
              const d = certDashboard;
              let nextStep = "";
              let nextCert = "";

              // Determine what's next
              if (!d.acc_ready) {
                nextCert = "ACC";
                if (p.acc_training_hours < d.requirements.acc_training_required) {
                  nextStep = `Complete coach training (${p.acc_training_hours}/${d.requirements.acc_training_required} hours)`;
                } else if (d.total_coaching_hours < d.requirements.acc_coaching_hours_required) {
                  nextStep = `Log more coaching hours (${d.total_coaching_hours}/${d.requirements.acc_coaching_hours_required})`;
                } else if (p.acc_mentor_hours < d.requirements.acc_mentor_hours_required) {
                  nextStep = `Complete mentor coaching (${p.acc_mentor_hours}/${d.requirements.acc_mentor_hours_required} hours)`;
                } else if (!p.acc_exam_passed) {
                  nextStep = "Pass the ICF Credentialing Exam";
                } else {
                  nextStep = "Submit ACC application";
                }
              } else if (!d.pcc_ready) {
                nextCert = "PCC";
                if ((p.acc_training_hours + p.pcc_training_hours) < d.requirements.pcc_training_required) {
                  nextStep = `Complete additional training (${p.acc_training_hours + p.pcc_training_hours}/${d.requirements.pcc_training_required} hours total)`;
                } else if (d.total_coaching_hours < d.requirements.pcc_coaching_hours_required) {
                  nextStep = `Log more coaching hours (${d.total_coaching_hours}/${d.requirements.pcc_coaching_hours_required})`;
                } else if (p.pcc_mentor_hours < d.requirements.pcc_mentor_hours_required) {
                  nextStep = `Complete PCC mentor coaching (${p.pcc_mentor_hours}/${d.requirements.pcc_mentor_hours_required} hours)`;
                } else if (!p.pcc_exam_passed) {
                  nextStep = "Pass the ICF Credentialing Exam (PCC level)";
                } else {
                  nextStep = "Submit PCC application";
                }
              } else {
                nextCert = "MCC";
                nextStep = "Continue building toward MCC requirements";
              }

              return (
                <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-purple-100 rounded-full">
                        <Target className="h-6 w-6 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg text-purple-900">What&apos;s Next: {nextCert}</h3>
                        <p className="text-purple-700 mt-1">{nextStep}</p>
                        <Button className="mt-3" size="sm" onClick={openProgressDialog}>
                          <Pencil className="h-4 w-4 mr-2" />
                          Update Progress
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* ACC Journey */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-purple-600" />
                  ACC - Associate Certified Coach
                  {certDashboard.acc_ready && <Badge className="bg-green-500 ml-2">Ready to Apply!</Badge>}
                  {certDashboard.progress.acc_credential_received && <Badge className="bg-purple-600 ml-2">Certified!</Badge>}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Step 1: Training */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.acc_training_hours >= certDashboard.requirements.acc_training_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.acc_training_hours >= certDashboard.requirements.acc_training_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.acc_training_hours >= certDashboard.requirements.acc_training_required ? <CheckCircle className="h-4 w-4" /> : '1'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete Coach-Specific Training</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.acc_training_hours}/{certDashboard.requirements.acc_training_required} hours {certDashboard.progress.acc_training_provider && `(${certDashboard.progress.acc_training_provider})`}</p>
                    <a href="https://coachingfederation.org/find-a-program" target="_blank" rel="noopener noreferrer" className="text-xs text-purple-600 hover:underline">Find ICF-accredited programs →</a>
                  </div>
                </div>

                {/* Step 2: Coaching Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_coaching_hours >= certDashboard.requirements.acc_coaching_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_coaching_hours >= certDashboard.requirements.acc_coaching_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_coaching_hours >= certDashboard.requirements.acc_coaching_hours_required ? <CheckCircle className="h-4 w-4" /> : '2'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Log 100+ Coaching Experience Hours</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_coaching_hours}/{certDashboard.requirements.acc_coaching_hours_required} hours logged</p>
                  </div>
                </div>

                {/* Step 3: Paid Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.paid_coaching_hours >= certDashboard.requirements.acc_paid_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.paid_coaching_hours >= certDashboard.requirements.acc_paid_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.paid_coaching_hours >= certDashboard.requirements.acc_paid_hours_required ? <CheckCircle className="h-4 w-4" /> : '3'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">75+ Hours Must Be Paid</p>
                    <p className="text-sm text-gray-600">{certDashboard.paid_coaching_hours}/{certDashboard.requirements.acc_paid_hours_required} paid hours</p>
                  </div>
                </div>

                {/* Step 4: Clients */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_clients >= certDashboard.requirements.acc_clients_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_clients >= certDashboard.requirements.acc_clients_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_clients >= certDashboard.requirements.acc_clients_required ? <CheckCircle className="h-4 w-4" /> : '4'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Coach 8+ Unique Clients</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_clients}/{certDashboard.requirements.acc_clients_required} clients</p>
                  </div>
                </div>

                {/* Step 5: Mentor Coaching */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.acc_mentor_hours >= certDashboard.requirements.acc_mentor_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.acc_mentor_hours >= certDashboard.requirements.acc_mentor_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.acc_mentor_hours >= certDashboard.requirements.acc_mentor_hours_required ? <CheckCircle className="h-4 w-4" /> : '5'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete 10 Hours Mentor Coaching</p>
                    <p className="text-sm text-gray-600">
                      {certDashboard.progress.acc_mentor_hours}/{certDashboard.requirements.acc_mentor_hours_required} hrs
                      (Individual: {certDashboard.progress.acc_mentor_individual_hours}/3 min, Group: {certDashboard.progress.acc_mentor_group_hours}/7 max)
                    </p>
                    {certDashboard.progress.acc_mentor_name && <p className="text-xs text-gray-500">Mentor: {certDashboard.progress.acc_mentor_name}</p>}
                  </div>
                </div>

                {/* Step 6: Exam */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.acc_exam_passed ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.acc_exam_passed ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.acc_exam_passed ? <CheckCircle className="h-4 w-4" /> : '6'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Pass ICF Credentialing Exam</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.acc_exam_passed ? 'Passed!' : 'Not yet taken'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/credentialing-exam" target="_blank" rel="noopener noreferrer" className="text-xs text-purple-600 hover:underline">Register for exam ($75) →</a>
                  </div>
                </div>

                {/* Step 7: Apply */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.acc_credential_received ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.acc_credential_received ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.acc_credential_received ? <CheckCircle className="h-4 w-4" /> : '7'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Submit ACC Application & Receive Credential</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.acc_credential_received ? `Certified! #${certDashboard.progress.acc_credential_number || 'N/A'}` : certDashboard.progress.acc_applied ? 'Application submitted' : 'Not yet applied'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/acc" target="_blank" rel="noopener noreferrer" className="text-xs text-purple-600 hover:underline">Apply for ACC ($175) →</a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* PCC Journey */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-amber-600" />
                  PCC - Professional Certified Coach
                  {certDashboard.pcc_ready && <Badge className="bg-green-500 ml-2">Ready to Apply!</Badge>}
                  {certDashboard.progress.pcc_credential_received && <Badge className="bg-amber-600 ml-2">Certified!</Badge>}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Step 1: Training */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours) >= certDashboard.requirements.pcc_training_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours) >= certDashboard.requirements.pcc_training_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours) >= certDashboard.requirements.pcc_training_required ? <CheckCircle className="h-4 w-4" /> : '1'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete 125+ Hours Coach Training</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours}/{certDashboard.requirements.pcc_training_required} total hours</p>
                  </div>
                </div>

                {/* Step 2: Coaching Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_coaching_hours >= certDashboard.requirements.pcc_coaching_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_coaching_hours >= certDashboard.requirements.pcc_coaching_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_coaching_hours >= certDashboard.requirements.pcc_coaching_hours_required ? <CheckCircle className="h-4 w-4" /> : '2'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Log 500+ Coaching Experience Hours</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_coaching_hours}/{certDashboard.requirements.pcc_coaching_hours_required} hours logged</p>
                  </div>
                </div>

                {/* Step 3: Paid Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.paid_coaching_hours >= certDashboard.requirements.pcc_paid_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.paid_coaching_hours >= certDashboard.requirements.pcc_paid_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.paid_coaching_hours >= certDashboard.requirements.pcc_paid_hours_required ? <CheckCircle className="h-4 w-4" /> : '3'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">450+ Hours Must Be Paid</p>
                    <p className="text-sm text-gray-600">{certDashboard.paid_coaching_hours}/{certDashboard.requirements.pcc_paid_hours_required} paid hours</p>
                  </div>
                </div>

                {/* Step 4: Clients */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_clients >= certDashboard.requirements.pcc_clients_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_clients >= certDashboard.requirements.pcc_clients_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_clients >= certDashboard.requirements.pcc_clients_required ? <CheckCircle className="h-4 w-4" /> : '4'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Coach 25+ Unique Clients</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_clients}/{certDashboard.requirements.pcc_clients_required} clients</p>
                  </div>
                </div>

                {/* Step 5: Mentor Coaching */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.pcc_mentor_hours >= certDashboard.requirements.pcc_mentor_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.pcc_mentor_hours >= certDashboard.requirements.pcc_mentor_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.pcc_mentor_hours >= certDashboard.requirements.pcc_mentor_hours_required ? <CheckCircle className="h-4 w-4" /> : '5'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete 10 Hours Mentor Coaching (PCC/MCC mentor)</p>
                    <p className="text-sm text-gray-600">
                      {certDashboard.progress.pcc_mentor_hours}/{certDashboard.requirements.pcc_mentor_hours_required} hrs
                      (Individual: {certDashboard.progress.pcc_mentor_individual_hours}/3 min, Group: {certDashboard.progress.pcc_mentor_group_hours}/7 max)
                    </p>
                    {certDashboard.progress.pcc_mentor_name && <p className="text-xs text-gray-500">Mentor: {certDashboard.progress.pcc_mentor_name}</p>}
                  </div>
                </div>

                {/* Step 6: Exam */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.pcc_exam_passed ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.pcc_exam_passed ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.pcc_exam_passed ? <CheckCircle className="h-4 w-4" /> : '6'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Pass ICF Credentialing Exam</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.pcc_exam_passed ? 'Passed!' : 'Not yet taken'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/credentialing-exam" target="_blank" rel="noopener noreferrer" className="text-xs text-amber-600 hover:underline">Register for exam ($75) →</a>
                  </div>
                </div>

                {/* Step 7: Apply */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.pcc_credential_received ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.pcc_credential_received ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.pcc_credential_received ? <CheckCircle className="h-4 w-4" /> : '7'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Submit PCC Application & Receive Credential</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.pcc_credential_received ? `Certified! #${certDashboard.progress.pcc_credential_number || 'N/A'}` : certDashboard.progress.pcc_applied ? 'Application submitted' : 'Not yet applied'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/pcc" target="_blank" rel="noopener noreferrer" className="text-xs text-amber-600 hover:underline">Apply for PCC ($300) →</a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* MCC Journey */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-emerald-600" />
                  MCC - Master Certified Coach
                  {certDashboard.mcc_ready && <Badge className="bg-green-500 ml-2">Ready to Apply!</Badge>}
                  {certDashboard.progress.mcc_credential_received && <Badge className="bg-emerald-600 ml-2">Certified!</Badge>}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Step 1: Training */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours + certDashboard.progress.mcc_training_hours) >= certDashboard.requirements.mcc_training_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours + certDashboard.progress.mcc_training_hours) >= certDashboard.requirements.mcc_training_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {(certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours + certDashboard.progress.mcc_training_hours) >= certDashboard.requirements.mcc_training_required ? <CheckCircle className="h-4 w-4" /> : '1'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete 200+ Hours Coach Training</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours + certDashboard.progress.mcc_training_hours}/{certDashboard.requirements.mcc_training_required} total hours</p>
                  </div>
                </div>

                {/* Step 2: Coaching Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_coaching_hours >= certDashboard.requirements.mcc_coaching_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_coaching_hours >= certDashboard.requirements.mcc_coaching_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_coaching_hours >= certDashboard.requirements.mcc_coaching_hours_required ? <CheckCircle className="h-4 w-4" /> : '2'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Log 2,500+ Coaching Experience Hours</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_coaching_hours}/{certDashboard.requirements.mcc_coaching_hours_required} hours logged</p>
                    <p className="text-xs text-gray-500">{(certDashboard.requirements.mcc_coaching_hours_required - certDashboard.total_coaching_hours).toFixed(1)} hours remaining</p>
                  </div>
                </div>

                {/* Step 3: Paid Hours */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.paid_coaching_hours >= certDashboard.requirements.mcc_paid_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.paid_coaching_hours >= certDashboard.requirements.mcc_paid_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.paid_coaching_hours >= certDashboard.requirements.mcc_paid_hours_required ? <CheckCircle className="h-4 w-4" /> : '3'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">2,250+ Hours Must Be Paid (90%)</p>
                    <p className="text-sm text-gray-600">{certDashboard.paid_coaching_hours}/{certDashboard.requirements.mcc_paid_hours_required} paid hours</p>
                  </div>
                </div>

                {/* Step 4: Clients */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.total_clients >= certDashboard.requirements.mcc_clients_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.total_clients >= certDashboard.requirements.mcc_clients_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.total_clients >= certDashboard.requirements.mcc_clients_required ? <CheckCircle className="h-4 w-4" /> : '4'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Coach 35+ Unique Clients</p>
                    <p className="text-sm text-gray-600">{certDashboard.total_clients}/{certDashboard.requirements.mcc_clients_required} clients</p>
                  </div>
                </div>

                {/* Step 5: Mentor Coaching */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.mcc_mentor_hours >= certDashboard.requirements.mcc_mentor_hours_required ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.mcc_mentor_hours >= certDashboard.requirements.mcc_mentor_hours_required ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.mcc_mentor_hours >= certDashboard.requirements.mcc_mentor_hours_required ? <CheckCircle className="h-4 w-4" /> : '5'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Complete 10 Hours Mentor Coaching (MCC mentor only)</p>
                    <p className="text-sm text-gray-600">
                      {certDashboard.progress.mcc_mentor_hours}/{certDashboard.requirements.mcc_mentor_hours_required} hrs
                      (Individual: {certDashboard.progress.mcc_mentor_individual_hours}/3 min, Group: {certDashboard.progress.mcc_mentor_group_hours}/7 max)
                    </p>
                    {certDashboard.progress.mcc_mentor_name && <p className="text-xs text-gray-500">Mentor: {certDashboard.progress.mcc_mentor_name}</p>}
                  </div>
                </div>

                {/* Step 6: Performance Evaluation */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.mcc_exam_passed ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.mcc_exam_passed ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.mcc_exam_passed ? <CheckCircle className="h-4 w-4" /> : '6'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Pass Performance Evaluation</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.mcc_exam_passed ? 'Passed!' : 'Not yet taken'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/mcc" target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-600 hover:underline">Learn about MCC requirements →</a>
                  </div>
                </div>

                {/* Step 7: Apply */}
                <div className={`flex items-start gap-3 p-3 rounded-lg ${certDashboard.progress.mcc_credential_received ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${certDashboard.progress.mcc_credential_received ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
                    {certDashboard.progress.mcc_credential_received ? <CheckCircle className="h-4 w-4" /> : '7'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Submit MCC Application & Receive Credential</p>
                    <p className="text-sm text-gray-600">{certDashboard.progress.mcc_credential_received ? `Certified! #${certDashboard.progress.mcc_credential_number || 'N/A'}` : certDashboard.progress.mcc_applied ? 'Application submitted' : 'Not yet applied'}</p>
                    <a href="https://coachingfederation.org/credentials-and-standards/mcc" target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-600 hover:underline">Apply for MCC ($450) →</a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resources Section */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  Helpful Resources
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <a href="https://coachingfederation.org/find-a-program" target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <GraduationCap className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="font-medium">Find Training Programs</p>
                      <p className="text-sm text-gray-500">ICF-accredited coach training</p>
                    </div>
                  </a>
                  <a href="https://coachingfederation.org/credentials-and-standards/credentialing-exam" target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <FileCheck className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">ICF Credentialing Exam</p>
                      <p className="text-sm text-gray-500">Register & prepare for exam</p>
                    </div>
                  </a>
                  <a href="https://coachingfederation.org/mentor-coaching" target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <Users className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">Find a Mentor Coach</p>
                      <p className="text-sm text-gray-500">ICF mentor coaching requirements</p>
                    </div>
                  </a>
                  <a href="https://coachingfederation.org/credentials-and-standards" target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                    <Award className="h-5 w-5 text-amber-600" />
                    <div>
                      <p className="font-medium">ICF Credentials Overview</p>
                      <p className="text-sm text-gray-500">ACC, PCC, MCC requirements</p>
                    </div>
                  </a>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Client Summary View */}
        {view === "clients" && (
          <>
            <Card className="mb-4">
              <CardContent className="pt-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search clients..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-0">
                <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Client</TableHead>
                    <TableHead className="text-right">Sessions</TableHead>
                    <TableHead className="text-right">Total Hours</TableHead>
                    <TableHead className="text-right">Paid</TableHead>
                    <TableHead className="text-right">Pro Bono</TableHead>
                    <TableHead className="text-right">Individual</TableHead>
                    <TableHead className="text-right">Group</TableHead>
                    <TableHead>First Session</TableHead>
                    <TableHead>Last Session</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : clientSummary.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8">
                        No coaching sessions recorded yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    clientSummary
                      .filter((client) =>
                        !search || client.client_name.toLowerCase().includes(search.toLowerCase())
                      )
                      .map((client) => (
                      <TableRow key={client.client_name}>
                        <TableCell className="font-medium">
                          {client.client_name}
                          {client.contact_id && (
                            <Badge variant="outline" className="ml-2 text-xs">
                              Linked
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">{client.total_sessions}</TableCell>
                        <TableCell className="text-right font-medium">{client.total_hours}</TableCell>
                        <TableCell className="text-right">{client.paid_hours}</TableCell>
                        <TableCell className="text-right">{client.pro_bono_hours}</TableCell>
                        <TableCell className="text-right">{client.individual_hours}</TableCell>
                        <TableCell className="text-right">{client.group_hours}</TableCell>
                        <TableCell>{client.first_session ? formatDate(client.first_session) : "-"}</TableCell>
                        <TableCell>{client.last_session ? formatDate(client.last_session) : "-"}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          </>
        )}

        {/* Sessions View */}
        {view === "sessions" && (
          <>
            {/* Filters */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search by client name..."
                        value={search}
                        onChange={(e) => {
                          setSearch(e.target.value);
                          setPage(1);
                        }}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select
                    value={sessionType}
                    onValueChange={(value) => {
                      setSessionType(value === "all" ? "" : value);
                      setPage(1);
                    }}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All types</SelectItem>
                      <SelectItem value="individual">Individual</SelectItem>
                      <SelectItem value="group">Group</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select
                    value={paymentType}
                    onValueChange={(value) => {
                      setPaymentType(value === "all" ? "" : value);
                      setPage(1);
                    }}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="All payments" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All payments</SelectItem>
                      <SelectItem value="paid">Paid</SelectItem>
                      <SelectItem value="pro_bono">Pro Bono</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Client</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Duration</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Verified</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8">
                          Loading...
                        </TableCell>
                      </TableRow>
                    ) : sessions.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8">
                          No sessions found
                        </TableCell>
                      </TableRow>
                    ) : (
                      sessions.map((session) => (
                        <TableRow key={session.id}>
                          <TableCell className="font-medium">
                            {session.client_name}
                          </TableCell>
                          <TableCell>{formatDate(session.session_date)}</TableCell>
                          <TableCell className="text-right">{session.duration_hours}h</TableCell>
                          <TableCell>
                            <Badge variant={session.session_type === "individual" ? "default" : "secondary"}>
                              {session.session_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={session.payment_type === "paid" ? "default" : "outline"}>
                              {session.payment_type === "paid" ? "Paid" : "Pro Bono"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-gray-500 text-sm">
                            {session.source}
                          </TableCell>
                          <TableCell>
                            {session.is_verified ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-gray-300" />
                            )}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => openEditDialog(session)}>
                                  <Pencil className="h-4 w-4 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleDeleteSession(session.id)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Pagination */}
            {total > 50 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing {(page - 1) * 50 + 1} to {Math.min(page * 50, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page * 50 >= total}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Summary View - Certification Progress */}
        {view === "summary" && summary && certDashboard && (
          <div className="space-y-6">
            {/* ACC, PCC, and MCC Status Cards */}
            <div className="grid md:grid-cols-3 gap-6">
              {/* ACC Card */}
              <Card className={certDashboard.acc_ready ? "border-green-500 border-2" : ""}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-purple-600" />
                      ACC - Associate Certified Coach
                    </CardTitle>
                    {certDashboard.acc_ready ? (
                      <Badge className="bg-green-500">Ready to Apply</Badge>
                    ) : (
                      <Badge variant="outline">In Progress</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Training */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <GraduationCap className="h-4 w-4" />
                        Coach Training
                      </span>
                      <span className={certDashboard.acc_training_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.acc_training_hours}/{certDashboard.requirements.acc_training_required} hrs
                        {certDashboard.acc_training_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.acc_training_progress >= 100 ? "bg-green-500" : "bg-purple-600"}`}
                        style={{ width: `${certDashboard.acc_training_progress}%` }} />
                    </div>
                  </div>

                  {/* Coaching Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        Coaching Hours
                      </span>
                      <span className={certDashboard.acc_coaching_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_coaching_hours}/{certDashboard.requirements.acc_coaching_hours_required} hrs
                        {certDashboard.acc_coaching_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.acc_coaching_progress >= 100 ? "bg-green-500" : "bg-purple-600"}`}
                        style={{ width: `${certDashboard.acc_coaching_progress}%` }} />
                    </div>
                  </div>

                  {/* Paid Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-4 w-4" />
                        Paid Hours
                      </span>
                      <span className={certDashboard.acc_paid_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.paid_coaching_hours}/{certDashboard.requirements.acc_paid_hours_required} hrs
                        {certDashboard.acc_paid_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.acc_paid_progress >= 100 ? "bg-green-500" : "bg-purple-600"}`}
                        style={{ width: `${certDashboard.acc_paid_progress}%` }} />
                    </div>
                  </div>

                  {/* Clients */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Unique Clients
                      </span>
                      <span className={certDashboard.acc_clients_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_clients}/{certDashboard.requirements.acc_clients_required}
                        {certDashboard.acc_clients_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.acc_clients_progress >= 100 ? "bg-green-500" : "bg-purple-600"}`}
                        style={{ width: `${certDashboard.acc_clients_progress}%` }} />
                    </div>
                  </div>

                  {/* Mentor Coaching */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <BookOpen className="h-4 w-4" />
                        Mentor Coaching
                      </span>
                      <span className={certDashboard.acc_mentor_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.acc_mentor_hours}/{certDashboard.requirements.acc_mentor_hours_required} hrs
                        {certDashboard.acc_mentor_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.acc_mentor_progress >= 100 ? "bg-green-500" : "bg-purple-600"}`}
                        style={{ width: `${certDashboard.acc_mentor_progress}%` }} />
                    </div>
                  </div>

                  {/* Exam */}
                  <div className="flex justify-between items-center text-sm pt-2 border-t">
                    <span className="flex items-center gap-1">
                      <FileCheck className="h-4 w-4" />
                      ICF Credentialing Exam
                    </span>
                    {certDashboard.progress.acc_exam_passed ? (
                      <Badge className="bg-green-500">Passed</Badge>
                    ) : (
                      <Badge variant="outline">Not Taken</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* PCC Card */}
              <Card className={certDashboard.pcc_ready ? "border-green-500 border-2" : ""}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-amber-600" />
                      PCC - Professional Certified Coach
                    </CardTitle>
                    {certDashboard.pcc_ready ? (
                      <Badge className="bg-green-500">Ready to Apply</Badge>
                    ) : (
                      <Badge variant="outline">In Progress</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Training */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <GraduationCap className="h-4 w-4" />
                        Coach Training
                      </span>
                      <span className={certDashboard.pcc_training_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours}/{certDashboard.requirements.pcc_training_required} hrs
                        {certDashboard.pcc_training_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.pcc_training_progress >= 100 ? "bg-green-500" : "bg-amber-500"}`}
                        style={{ width: `${certDashboard.pcc_training_progress}%` }} />
                    </div>
                  </div>

                  {/* Coaching Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        Coaching Hours
                      </span>
                      <span className={certDashboard.pcc_coaching_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_coaching_hours}/{certDashboard.requirements.pcc_coaching_hours_required} hrs
                        {certDashboard.pcc_coaching_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.pcc_coaching_progress >= 100 ? "bg-green-500" : "bg-amber-500"}`}
                        style={{ width: `${certDashboard.pcc_coaching_progress}%` }} />
                    </div>
                  </div>

                  {/* Paid Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-4 w-4" />
                        Paid Hours
                      </span>
                      <span className={certDashboard.pcc_paid_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.paid_coaching_hours}/{certDashboard.requirements.pcc_paid_hours_required} hrs
                        {certDashboard.pcc_paid_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.pcc_paid_progress >= 100 ? "bg-green-500" : "bg-amber-500"}`}
                        style={{ width: `${certDashboard.pcc_paid_progress}%` }} />
                    </div>
                  </div>

                  {/* Clients */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Unique Clients
                      </span>
                      <span className={certDashboard.pcc_clients_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_clients}/{certDashboard.requirements.pcc_clients_required}
                        {certDashboard.pcc_clients_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.pcc_clients_progress >= 100 ? "bg-green-500" : "bg-amber-500"}`}
                        style={{ width: `${certDashboard.pcc_clients_progress}%` }} />
                    </div>
                  </div>

                  {/* Mentor Coaching */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <BookOpen className="h-4 w-4" />
                        Mentor Coaching (PCC/MCC)
                      </span>
                      <span className={certDashboard.pcc_mentor_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.pcc_mentor_hours}/{certDashboard.requirements.pcc_mentor_hours_required} hrs
                        {certDashboard.pcc_mentor_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.pcc_mentor_progress >= 100 ? "bg-green-500" : "bg-amber-500"}`}
                        style={{ width: `${certDashboard.pcc_mentor_progress}%` }} />
                    </div>
                  </div>

                  {/* Exam */}
                  <div className="flex justify-between items-center text-sm pt-2 border-t">
                    <span className="flex items-center gap-1">
                      <FileCheck className="h-4 w-4" />
                      ICF Credentialing Exam
                    </span>
                    {certDashboard.progress.pcc_exam_passed ? (
                      <Badge className="bg-green-500">Passed</Badge>
                    ) : (
                      <Badge variant="outline">Not Taken</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* MCC Card */}
              <Card className={certDashboard.mcc_ready ? "border-green-500 border-2" : ""}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-emerald-600" />
                      MCC - Master Certified Coach
                    </CardTitle>
                    {certDashboard.mcc_ready ? (
                      <Badge className="bg-green-500">Ready to Apply</Badge>
                    ) : (
                      <Badge variant="outline">In Progress</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Training */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <GraduationCap className="h-4 w-4" />
                        Coach Training
                      </span>
                      <span className={certDashboard.mcc_training_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.acc_training_hours + certDashboard.progress.pcc_training_hours + (certDashboard.progress.mcc_training_hours || 0)}/{certDashboard.requirements.mcc_training_required} hrs
                        {certDashboard.mcc_training_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.mcc_training_progress >= 100 ? "bg-green-500" : "bg-emerald-500"}`}
                        style={{ width: `${certDashboard.mcc_training_progress}%` }} />
                    </div>
                  </div>

                  {/* Coaching Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        Coaching Hours
                      </span>
                      <span className={certDashboard.mcc_coaching_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_coaching_hours}/{certDashboard.requirements.mcc_coaching_hours_required} hrs
                        {certDashboard.mcc_coaching_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.mcc_coaching_progress >= 100 ? "bg-green-500" : "bg-emerald-500"}`}
                        style={{ width: `${certDashboard.mcc_coaching_progress}%` }} />
                    </div>
                  </div>

                  {/* Paid Hours */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-4 w-4" />
                        Paid Hours
                      </span>
                      <span className={certDashboard.mcc_paid_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.paid_coaching_hours}/{certDashboard.requirements.mcc_paid_hours_required} hrs
                        {certDashboard.mcc_paid_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.mcc_paid_progress >= 100 ? "bg-green-500" : "bg-emerald-500"}`}
                        style={{ width: `${certDashboard.mcc_paid_progress}%` }} />
                    </div>
                  </div>

                  {/* Clients */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Unique Clients
                      </span>
                      <span className={certDashboard.mcc_clients_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.total_clients}/{certDashboard.requirements.mcc_clients_required}
                        {certDashboard.mcc_clients_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.mcc_clients_progress >= 100 ? "bg-green-500" : "bg-emerald-500"}`}
                        style={{ width: `${certDashboard.mcc_clients_progress}%` }} />
                    </div>
                  </div>

                  {/* Mentor Coaching */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-1">
                        <BookOpen className="h-4 w-4" />
                        Mentor Coaching (MCC)
                      </span>
                      <span className={certDashboard.mcc_mentor_progress >= 100 ? "text-green-600 font-medium" : ""}>
                        {certDashboard.progress.mcc_mentor_hours || 0}/{certDashboard.requirements.mcc_mentor_hours_required} hrs
                        {certDashboard.mcc_mentor_progress >= 100 && <CheckCircle className="h-4 w-4 inline ml-1" />}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${certDashboard.mcc_mentor_progress >= 100 ? "bg-green-500" : "bg-emerald-500"}`}
                        style={{ width: `${certDashboard.mcc_mentor_progress}%` }} />
                    </div>
                  </div>

                  {/* Exam */}
                  <div className="flex justify-between items-center text-sm pt-2 border-t">
                    <span className="flex items-center gap-1">
                      <FileCheck className="h-4 w-4" />
                      Performance Evaluation
                    </span>
                    {certDashboard.progress.mcc_exam_passed ? (
                      <Badge className="bg-green-500">Passed</Badge>
                    ) : (
                      <Badge variant="outline">Not Taken</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Hours Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Hours Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Individual Coaching</span>
                      <span className="font-medium">{summary.individual_hours} hours</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(summary.individual_hours / summary.total_hours) * 100}%`,
                        }}
                      />
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Group Coaching</span>
                      <span className="font-medium">{summary.group_hours} hours</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{
                          width: `${(summary.group_hours / summary.total_hours) * 100}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Paid Hours</span>
                      <span className="font-medium">{summary.paid_hours} hours</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-emerald-600 h-2 rounded-full"
                        style={{
                          width: `${(summary.paid_hours / summary.total_hours) * 100}%`,
                        }}
                      />
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Pro Bono Hours</span>
                      <span className="font-medium">{summary.pro_bono_hours} hours</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-pink-600 h-2 rounded-full"
                        style={{
                          width: `${(summary.pro_bono_hours / summary.total_hours) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={showAddDialog || !!editSession} onOpenChange={(open) => {
          if (!open) {
            setShowAddDialog(false);
            setEditSession(null);
            resetForm();
          }
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editSession ? "Edit Session" : "Add Coaching Session"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Client Name *</Label>
                <Input
                  value={formData.client_name}
                  onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                  placeholder="Enter client name"
                />
              </div>

              <div className="space-y-2">
                <Label>Client Email</Label>
                <Input
                  type="email"
                  value={formData.client_email || ""}
                  onChange={(e) => setFormData({ ...formData, client_email: e.target.value })}
                  placeholder="client@example.com"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Session Date *</Label>
                  <Input
                    type="date"
                    value={formData.session_date}
                    onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Duration (hours) *</Label>
                  <Input
                    type="number"
                    step="0.25"
                    min="0.25"
                    max="8"
                    value={formData.duration_hours}
                    onChange={(e) => setFormData({ ...formData, duration_hours: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Session Type</Label>
                  <Select
                    value={formData.session_type}
                    onValueChange={(value) => setFormData({ ...formData, session_type: value as "individual" | "group" })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="individual">Individual</SelectItem>
                      <SelectItem value="group">Group</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Payment Type</Label>
                  <Select
                    value={formData.payment_type}
                    onValueChange={(value) => setFormData({ ...formData, payment_type: value as "paid" | "pro_bono" })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="paid">Paid</SelectItem>
                      <SelectItem value="pro_bono">Pro Bono</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {formData.session_type === "group" && (
                <div className="space-y-2">
                  <Label>Group Size</Label>
                  <Input
                    type="number"
                    min="2"
                    value={formData.group_size || ""}
                    onChange={(e) => setFormData({ ...formData, group_size: parseInt(e.target.value) || undefined })}
                    placeholder="Number of participants"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label>Meeting Title</Label>
                <Input
                  value={formData.meeting_title || ""}
                  onChange={(e) => setFormData({ ...formData, meeting_title: e.target.value })}
                  placeholder="Optional meeting title"
                />
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes || ""}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Optional notes about the session"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowAddDialog(false);
                setEditSession(null);
                resetForm();
              }}>
                Cancel
              </Button>
              <Button onClick={editSession ? handleUpdateSession : handleAddSession}>
                {editSession ? "Update" : "Add Session"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Progress Dialog */}
        <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Certification Progress</DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* ACC Section */}
              <div className="space-y-4">
                <h3 className="font-semibold text-purple-600 flex items-center gap-2">
                  <Award className="h-4 w-4" />
                  ACC Requirements
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Training Hours</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.acc_training_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_training_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Training Provider</Label>
                    <Input
                      value={progressFormData.acc_training_provider}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_training_provider: e.target.value })}
                      placeholder="e.g., CTI, IPEC"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Hours (Total)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.acc_mentor_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_mentor_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Individual (min 3)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.acc_mentor_individual_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_mentor_individual_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Group (max 7)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.acc_mentor_group_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_mentor_group_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Coach Name</Label>
                    <Input
                      value={progressFormData.acc_mentor_name}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_mentor_name: e.target.value })}
                    />
                  </div>
                  <div className="flex items-center space-x-2 pt-6">
                    <input
                      type="checkbox"
                      id="acc_exam"
                      checked={progressFormData.acc_exam_passed}
                      onChange={(e) => setProgressFormData({ ...progressFormData, acc_exam_passed: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="acc_exam">ICF Exam Passed</Label>
                  </div>
                </div>
              </div>

              <div className="border-t pt-4" />

              {/* PCC Section */}
              <div className="space-y-4">
                <h3 className="font-semibold text-amber-600 flex items-center gap-2">
                  <Award className="h-4 w-4" />
                  PCC Requirements
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Additional Training Hours</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.pcc_training_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_training_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Training Provider</Label>
                    <Input
                      value={progressFormData.pcc_training_provider}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_training_provider: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Hours (Total)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.pcc_mentor_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_mentor_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Individual (min 3)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.pcc_mentor_individual_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_mentor_individual_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Group (max 7)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.pcc_mentor_group_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_mentor_group_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Coach Name (PCC/MCC)</Label>
                    <Input
                      value={progressFormData.pcc_mentor_name}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_mentor_name: e.target.value })}
                    />
                  </div>
                  <div className="flex items-center space-x-2 pt-6">
                    <input
                      type="checkbox"
                      id="pcc_exam"
                      checked={progressFormData.pcc_exam_passed}
                      onChange={(e) => setProgressFormData({ ...progressFormData, pcc_exam_passed: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="pcc_exam">ICF Exam Passed</Label>
                  </div>
                </div>
              </div>

              <div className="border-t pt-4" />

              {/* MCC Section */}
              <div className="space-y-4">
                <h3 className="font-semibold text-emerald-600 flex items-center gap-2">
                  <Award className="h-4 w-4" />
                  MCC Requirements
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Additional Training Hours</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.mcc_training_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_training_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Training Provider</Label>
                    <Input
                      value={progressFormData.mcc_training_provider}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_training_provider: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Hours (Total)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.mcc_mentor_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_mentor_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Individual (min 3)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.mcc_mentor_individual_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_mentor_individual_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Group (max 7)</Label>
                    <Input
                      type="number"
                      step="0.5"
                      value={progressFormData.mcc_mentor_group_hours}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_mentor_group_hours: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Mentor Coach Name (MCC only)</Label>
                    <Input
                      value={progressFormData.mcc_mentor_name}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_mentor_name: e.target.value })}
                    />
                  </div>
                  <div className="flex items-center space-x-2 pt-6">
                    <input
                      type="checkbox"
                      id="mcc_exam"
                      checked={progressFormData.mcc_exam_passed}
                      onChange={(e) => setProgressFormData({ ...progressFormData, mcc_exam_passed: e.target.checked })}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="mcc_exam">Performance Evaluation Passed</Label>
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowProgressDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveProgress}>
                Save Progress
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Shell>
  );
}
