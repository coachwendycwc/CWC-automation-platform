"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { contractorsApi } from "@/lib/api";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Users, Pencil, Trash2, ArrowLeft, DollarSign, FileText, Search, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

interface Contractor {
  id: string;
  name: string;
  business_name: string | null;
  email: string | null;
  phone: string | null;
  tax_id: string | null;
  tax_id_type: string;
  w9_on_file: boolean;
  w9_received_date: string | null;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  service_type: string | null;
  is_active: boolean;
  notes: string | null;
  total_paid_ytd: number;
}

interface Payment {
  id: string;
  contractor_id: string;
  amount: number;
  payment_date: string;
  description: string;
  payment_method: string;
  reference: string | null;
  invoice_number: string | null;
  tax_year: number;
}

export default function ContractorsPage() {
  const { token } = useAuth();
  const currentYear = new Date().getFullYear();
  const [contractors, setContractors] = useState<Contractor[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [editingContractor, setEditingContractor] = useState<Contractor | null>(null);
  const [selectedContractor, setSelectedContractor] = useState<Contractor | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary1099, setSummary1099] = useState<any[]>([]);
  const [taxYear, setTaxYear] = useState(currentYear);

  // Contractor form state
  const [formData, setFormData] = useState({
    name: "",
    business_name: "",
    email: "",
    phone: "",
    tax_id: "",
    tax_id_type: "ein",
    w9_on_file: false,
    w9_received_date: "",
    address_line1: "",
    city: "",
    state: "",
    zip_code: "",
    service_type: "",
    notes: "",
  });

  // Payment form state
  const [paymentForm, setPaymentForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "bank_transfer",
    reference: "",
    invoice_number: "",
    create_expense: true,
  });

  useEffect(() => {
    if (token) {
      loadContractors();
      load1099Summary();
    }
  }, [token, showInactive, taxYear]);

  const loadContractors = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await contractorsApi.list(token, {
        is_active: showInactive ? undefined : true,
        search: search || undefined,
      });
      setContractors(data.items);
    } catch (error) {
      console.error("Failed to load contractors:", error);
    } finally {
      setLoading(false);
    }
  };

  const load1099Summary = async () => {
    if (!token) return;
    try {
      const data = await contractorsApi.get1099Summary(token, taxYear);
      setSummary1099(data);
    } catch (error) {
      console.error("Failed to load 1099 summary:", error);
    }
  };

  const loadPayments = async (contractorId: string) => {
    if (!token) return;
    try {
      const data = await contractorsApi.listPayments(token, contractorId, taxYear);
      setPayments(data);
    } catch (error) {
      console.error("Failed to load payments:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      if (editingContractor) {
        await contractorsApi.update(token, editingContractor.id, formData);
        toast.success("Contractor updated");
      } else {
        await contractorsApi.create(token, formData);
        toast.success("Contractor added");
      }

      setDialogOpen(false);
      resetForm();
      loadContractors();
    } catch (error) {
      toast.error("Failed to save contractor");
    }
  };

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedContractor) return;

    try {
      await contractorsApi.createPayment(token, {
        contractor_id: selectedContractor.id,
        amount: parseFloat(paymentForm.amount),
        payment_date: paymentForm.payment_date,
        description: paymentForm.description,
        payment_method: paymentForm.payment_method,
        reference: paymentForm.reference || null,
        invoice_number: paymentForm.invoice_number || null,
        create_expense: paymentForm.create_expense,
      });
      toast.success("Payment recorded");
      setPaymentDialogOpen(false);
      resetPaymentForm();
      loadContractors();
      loadPayments(selectedContractor.id);
      load1099Summary();
    } catch (error) {
      toast.error("Failed to record payment");
    }
  };

  const handleEdit = (contractor: Contractor) => {
    setEditingContractor(contractor);
    setFormData({
      name: contractor.name,
      business_name: contractor.business_name || "",
      email: contractor.email || "",
      phone: contractor.phone || "",
      tax_id: contractor.tax_id || "",
      tax_id_type: contractor.tax_id_type,
      w9_on_file: contractor.w9_on_file,
      w9_received_date: contractor.w9_received_date || "",
      address_line1: contractor.address_line1 || "",
      city: contractor.city || "",
      state: contractor.state || "",
      zip_code: contractor.zip_code || "",
      service_type: contractor.service_type || "",
      notes: contractor.notes || "",
    });
    setDialogOpen(true);
  };

  const handleDeactivate = async (id: string) => {
    if (!token || !confirm("Are you sure you want to deactivate this contractor?")) return;
    try {
      await contractorsApi.delete(token, id);
      toast.success("Contractor deactivated");
      loadContractors();
    } catch (error) {
      toast.error("Failed to deactivate contractor");
    }
  };

  const openPaymentDialog = (contractor: Contractor) => {
    setSelectedContractor(contractor);
    loadPayments(contractor.id);
    setPaymentDialogOpen(true);
  };

  const resetForm = () => {
    setEditingContractor(null);
    setFormData({
      name: "",
      business_name: "",
      email: "",
      phone: "",
      tax_id: "",
      tax_id_type: "ein",
      w9_on_file: false,
      w9_received_date: "",
      address_line1: "",
      city: "",
      state: "",
      zip_code: "",
      service_type: "",
      notes: "",
    });
  };

  const resetPaymentForm = () => {
    setPaymentForm({
      amount: "",
      payment_date: new Date().toISOString().split("T")[0],
      description: "",
      payment_method: "bank_transfer",
      reference: "",
      invoice_number: "",
      create_expense: true,
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const needs1099Count = summary1099.filter((c) => c.needs_1099).length;

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
          <h1 className="text-3xl font-bold">1099 Contractors</h1>
          <p className="text-muted-foreground">Manage contractors and track payments for tax reporting</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Contractor
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>{editingContractor ? "Edit Contractor" : "Add Contractor"}</DialogTitle>
                <DialogDescription>
                  {editingContractor ? "Update contractor details" : "Add a new 1099 contractor"}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="business_name">Business Name</Label>
                    <Input
                      id="business_name"
                      value={formData.business_name}
                      onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="tax_id">Tax ID (SSN/EIN)</Label>
                    <Input
                      id="tax_id"
                      value={formData.tax_id}
                      onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                      placeholder="XX-XXXXXXX"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="tax_id_type">ID Type</Label>
                    <Select
                      value={formData.tax_id_type}
                      onValueChange={(v) => setFormData({ ...formData, tax_id_type: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ein">EIN</SelectItem>
                        <SelectItem value="ssn">SSN</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="w9_on_file"
                      checked={formData.w9_on_file}
                      onCheckedChange={(checked) => setFormData({ ...formData, w9_on_file: checked as boolean })}
                    />
                    <Label htmlFor="w9_on_file">W-9 on file</Label>
                  </div>
                  {formData.w9_on_file && (
                    <div className="grid gap-2">
                      <Label htmlFor="w9_received_date">W-9 Received</Label>
                      <Input
                        id="w9_received_date"
                        type="date"
                        value={formData.w9_received_date}
                        onChange={(e) => setFormData({ ...formData, w9_received_date: e.target.value })}
                      />
                    </div>
                  )}
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="address_line1">Address</Label>
                  <Input
                    id="address_line1"
                    value={formData.address_line1}
                    onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                      maxLength={2}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="zip_code">ZIP</Label>
                    <Input
                      id="zip_code"
                      value={formData.zip_code}
                      onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="service_type">Service Type</Label>
                  <Input
                    id="service_type"
                    value={formData.service_type}
                    onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                    placeholder="e.g., Web Development, Consulting"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">{editingContractor ? "Update" : "Add"} Contractor</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* 1099 Alert */}
      {needs1099Count > 0 && (
        <Card className="border-yellow-500 bg-yellow-50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              1099 Forms Required
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-yellow-700">
              {needs1099Count} contractor{needs1099Count > 1 ? "s have" : " has"} been paid $600 or more in {taxYear} and will need a 1099-NEC form.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Contractors</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{contractors.filter(c => c.is_active).length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Paid ({taxYear})</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(summary1099.reduce((sum, c) => sum + c.total_paid, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Need 1099</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{needs1099Count}</div>
            <p className="text-xs text-muted-foreground">Paid $600+ in {taxYear}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search contractors..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyUp={(e) => e.key === "Enter" && loadContractors()}
                  className="pl-10"
                />
              </div>
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
            <div className="flex items-center space-x-2">
              <Checkbox
                id="showInactive"
                checked={showInactive}
                onCheckedChange={(checked) => setShowInactive(checked as boolean)}
              />
              <Label htmlFor="showInactive">Show inactive</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contractors Table */}
      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : contractors.length === 0 ? (
            <div className="text-center py-8">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No contractors found</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Contractor
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Service</TableHead>
                  <TableHead>W-9</TableHead>
                  <TableHead className="text-right">YTD Paid</TableHead>
                  <TableHead>1099</TableHead>
                  <TableHead className="w-32"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {contractors.map((contractor) => {
                  const summary = summary1099.find(s => s.contractor_id === contractor.id);
                  const totalPaid = summary?.total_paid || 0;
                  const needs1099 = totalPaid >= 600;

                  return (
                    <TableRow key={contractor.id} className={!contractor.is_active ? "opacity-50" : ""}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{contractor.name}</div>
                          {contractor.business_name && (
                            <div className="text-sm text-muted-foreground">{contractor.business_name}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{contractor.service_type || "—"}</TableCell>
                      <TableCell>
                        {contractor.w9_on_file ? (
                          <Badge variant="default" className="bg-green-100 text-green-800">On File</Badge>
                        ) : (
                          <Badge variant="destructive">Missing</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(totalPaid)}
                      </TableCell>
                      <TableCell>
                        {needs1099 ? (
                          <Badge variant="default" className="bg-yellow-100 text-yellow-800">Required</Badge>
                        ) : (
                          <Badge variant="secondary">N/A</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => openPaymentDialog(contractor)} title="Record Payment">
                            <DollarSign className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(contractor)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          {contractor.is_active && (
                            <Button variant="ghost" size="icon" onClick={() => handleDeactivate(contractor.id)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={(open) => {
        setPaymentDialogOpen(open);
        if (!open) {
          setSelectedContractor(null);
          resetPaymentForm();
        }
      }}>
        <DialogContent className="max-w-lg">
          {selectedContractor && (
            <Tabs defaultValue="record">
              <DialogHeader>
                <DialogTitle>Payments - {selectedContractor.name}</DialogTitle>
                <TabsList className="mt-2">
                  <TabsTrigger value="record">Record Payment</TabsTrigger>
                  <TabsTrigger value="history">History ({payments.length})</TabsTrigger>
                </TabsList>
              </DialogHeader>

              <TabsContent value="record">
                <form onSubmit={handlePaymentSubmit}>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="pay_amount">Amount *</Label>
                        <Input
                          id="pay_amount"
                          type="number"
                          step="0.01"
                          value={paymentForm.amount}
                          onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                          required
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="pay_date">Date *</Label>
                        <Input
                          id="pay_date"
                          type="date"
                          value={paymentForm.payment_date}
                          onChange={(e) => setPaymentForm({ ...paymentForm, payment_date: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="pay_description">Description *</Label>
                      <Input
                        id="pay_description"
                        value={paymentForm.description}
                        onChange={(e) => setPaymentForm({ ...paymentForm, description: e.target.value })}
                        placeholder="What was this payment for?"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="pay_method">Payment Method</Label>
                        <Select
                          value={paymentForm.payment_method}
                          onValueChange={(v) => setPaymentForm({ ...paymentForm, payment_method: v })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                            <SelectItem value="check">Check</SelectItem>
                            <SelectItem value="paypal">PayPal</SelectItem>
                            <SelectItem value="venmo">Venmo</SelectItem>
                            <SelectItem value="zelle">Zelle</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="pay_invoice">Invoice #</Label>
                        <Input
                          id="pay_invoice"
                          value={paymentForm.invoice_number}
                          onChange={(e) => setPaymentForm({ ...paymentForm, invoice_number: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="create_expense"
                        checked={paymentForm.create_expense}
                        onCheckedChange={(checked) => setPaymentForm({ ...paymentForm, create_expense: checked as boolean })}
                      />
                      <Label htmlFor="create_expense">Also create expense record</Label>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setPaymentDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit">Record Payment</Button>
                  </DialogFooter>
                </form>
              </TabsContent>

              <TabsContent value="history">
                <div className="py-4">
                  {payments.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">No payments recorded for {taxYear}</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {payments.map((payment) => (
                          <TableRow key={payment.id}>
                            <TableCell>{new Date(payment.payment_date).toLocaleDateString()}</TableCell>
                            <TableCell>{payment.description}</TableCell>
                            <TableCell className="text-right">{formatCurrency(payment.amount)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
    </Shell>
  );
}
