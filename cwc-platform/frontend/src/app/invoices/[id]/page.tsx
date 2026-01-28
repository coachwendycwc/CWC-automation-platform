"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { invoicesApi, paymentsApi, contactsApi } from "@/lib/api";
import {
  ArrowLeft,
  Send,
  Copy,
  Trash2,
  ExternalLink,
  Plus,
  DollarSign,
  X,
} from "lucide-react";
import Link from "next/link";

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
  service_type?: string;
}

interface Payment {
  id: string;
  amount: number;
  payment_method: string;
  payment_date: string;
  reference?: string;
  notes?: string;
  created_at: string;
}

interface Invoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  organization_id: string | null;
  line_items: LineItem[];
  subtotal: number;
  tax_rate: number | null;
  tax_amount: number;
  discount_amount: number;
  total: number;
  amount_paid: number;
  balance_due: number;
  payment_terms: string;
  due_date: string;
  status: string;
  sent_at: string | null;
  viewed_at: string | null;
  paid_at: string | null;
  is_payment_plan: boolean;
  view_token: string;
  notes: string | null;
  memo: string | null;
  created_at: string;
  updated_at: string;
}

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  viewed: "bg-purple-100 text-purple-800",
  partial: "bg-yellow-100 text-yellow-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-500",
};

const PAYMENT_TERMS_LABELS: Record<string, string> = {
  due_on_receipt: "Due on Receipt",
  net_15: "Net 15",
  net_30: "Net 30",
  "50_50_split": "50/50 Split",
};

const PAYMENT_METHODS = [
  { value: "card", label: "Credit/Debit Card" },
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "cash", label: "Cash" },
  { value: "check", label: "Check" },
  { value: "other", label: "Other" },
];

export default function InvoiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [contact, setContact] = useState<Contact | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // Payment form state
  const [paymentAmount, setPaymentAmount] = useState<string>("");
  const [paymentMethod, setPaymentMethod] = useState<string>("other");
  const [paymentDate, setPaymentDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [paymentReference, setPaymentReference] = useState<string>("");
  const [paymentNotes, setPaymentNotes] = useState<string>("");
  const [recordingPayment, setRecordingPayment] = useState(false);

  useEffect(() => {
    if (params.id) {
      loadInvoice(params.id as string);
    }
  }, [params.id]);

  const loadInvoice = async (id: string) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const invoiceData = await invoicesApi.get(token, id);
      setInvoice(invoiceData);

      // Load contact
      const contactData = await contactsApi.get(token, invoiceData.contact_id);
      setContact(contactData);

      // Load payments
      const paymentsData = await paymentsApi.listForInvoice(token, id);
      setPayments(paymentsData);
    } catch (err) {
      console.error("Failed to load invoice:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!invoice) return;
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.send(token, invoice.id);
      toast.success("Invoice sent successfully");
      await loadInvoice(invoice.id);
    } catch (err: any) {
      toast.error(err.message || "Failed to send invoice");
    }
  };

  const handleDuplicate = async () => {
    if (!invoice) return;
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      const newInvoice = await invoicesApi.duplicate(token, invoice.id);
      toast.success("Invoice duplicated");
      router.push(`/invoices/${newInvoice.id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to duplicate invoice");
    }
  };

  const handleDelete = async () => {
    if (!invoice) return;
    if (!confirm("Are you sure you want to delete this invoice?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.delete(token, invoice.id);
      toast.success("Invoice deleted");
      router.push("/invoices");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete invoice");
    }
  };

  const handleCancel = async () => {
    if (!invoice) return;
    if (!confirm("Are you sure you want to cancel this invoice?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await invoicesApi.cancel(token, invoice.id);
      toast.success("Invoice cancelled");
      await loadInvoice(invoice.id);
    } catch (err: any) {
      toast.error(err.message || "Failed to cancel invoice");
    }
  };

  const handleRecordPayment = async () => {
    if (!invoice) return;
    const amount = parseFloat(paymentAmount);
    if (!amount || amount <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    setRecordingPayment(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      await paymentsApi.record(token, invoice.id, {
        amount,
        payment_method: paymentMethod,
        payment_date: paymentDate,
        reference: paymentReference || null,
        notes: paymentNotes || null,
      });

      setShowPaymentModal(false);
      setPaymentAmount("");
      setPaymentMethod("other");
      setPaymentReference("");
      setPaymentNotes("");
      toast.success("Payment recorded");
      await loadInvoice(invoice.id);
    } catch (err: any) {
      toast.error(err.message || "Failed to record payment");
    } finally {
      setRecordingPayment(false);
    }
  };

  const handleDeletePayment = async (paymentId: string) => {
    if (!confirm("Are you sure you want to delete this payment?")) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      await paymentsApi.delete(token, paymentId);
      toast.success("Payment deleted");
      await loadInvoice(invoice!.id);
    } catch (err: any) {
      toast.error(err.message || "Failed to delete payment");
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getPublicUrl = () => {
    if (!invoice) return "";
    return `${window.location.origin}/pay/${invoice.view_token}`;
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

  if (!invoice) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Invoice not found</div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/invoices">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{invoice.invoice_number}</h1>
                <Badge className={STATUS_COLORS[invoice.status]}>{invoice.status}</Badge>
              </div>
              <p className="text-gray-600">
                Created {formatDate(invoice.created_at)}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            {invoice.status === "draft" && (
              <>
                <Button variant="outline" onClick={handleSend}>
                  <Send className="h-4 w-4 mr-2" />
                  Send
                </Button>
                <Button variant="outline" onClick={handleDelete} className="text-red-600">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </>
            )}
            {invoice.status !== "draft" && invoice.status !== "cancelled" && invoice.status !== "paid" && (
              <>
                <Button onClick={() => {
                  setPaymentAmount(invoice.balance_due.toString());
                  setShowPaymentModal(true);
                }}>
                  <DollarSign className="h-4 w-4 mr-2" />
                  Record Payment
                </Button>
                <Button variant="outline" onClick={handleCancel}>
                  <X className="h-4 w-4 mr-2" />
                  Cancel Invoice
                </Button>
              </>
            )}
            <Button variant="outline" onClick={handleDuplicate}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicate
            </Button>
            {invoice.status !== "draft" && (
              <Button variant="outline" onClick={() => window.open(getPublicUrl(), "_blank")}>
                <ExternalLink className="h-4 w-4 mr-2" />
                View Public
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2 space-y-6">
            {/* Client Info */}
            <Card>
              <CardHeader>
                <CardTitle>Bill To</CardTitle>
              </CardHeader>
              <CardContent>
                {contact && (
                  <div>
                    <p className="font-medium text-gray-900">
                      {contact.first_name} {contact.last_name || ""}
                    </p>
                    {contact.email && <p className="text-gray-500">{contact.email}</p>}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Line Items */}
            <Card>
              <CardHeader>
                <CardTitle>Line Items</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="border-b">
                    <tr className="text-left text-xs font-medium text-gray-500 uppercase">
                      <th className="pb-2">Description</th>
                      <th className="pb-2 text-center">Qty</th>
                      <th className="pb-2 text-right">Unit Price</th>
                      <th className="pb-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {invoice.line_items.map((item, index) => (
                      <tr key={index}>
                        <td className="py-3">
                          <div className="font-medium text-gray-900">{item.description}</div>
                          {item.service_type && (
                            <div className="text-sm text-gray-500 capitalize">{item.service_type}</div>
                          )}
                        </td>
                        <td className="py-3 text-center text-gray-600">{item.quantity}</td>
                        <td className="py-3 text-right text-gray-600">{formatCurrency(item.unit_price)}</td>
                        <td className="py-3 text-right font-medium">{formatCurrency(item.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Totals */}
                <div className="mt-6 border-t pt-4">
                  <div className="flex justify-end">
                    <div className="w-64 space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Subtotal</span>
                        <span>{formatCurrency(invoice.subtotal)}</span>
                      </div>
                      {invoice.tax_rate && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Tax ({invoice.tax_rate}%)</span>
                          <span>{formatCurrency(invoice.tax_amount)}</span>
                        </div>
                      )}
                      {invoice.discount_amount > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Discount</span>
                          <span className="text-red-500">-{formatCurrency(invoice.discount_amount)}</span>
                        </div>
                      )}
                      <div className="border-t pt-2 flex justify-between font-bold text-lg">
                        <span>Total</span>
                        <span>{formatCurrency(invoice.total)}</span>
                      </div>
                      {invoice.amount_paid > 0 && (
                        <>
                          <div className="flex justify-between text-sm text-green-600">
                            <span>Paid</span>
                            <span>-{formatCurrency(invoice.amount_paid)}</span>
                          </div>
                          <div className="flex justify-between font-bold">
                            <span>Balance Due</span>
                            <span>{formatCurrency(invoice.balance_due)}</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Payments */}
            {payments.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Payments</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {payments.map((payment) => (
                      <div key={payment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-green-600">
                              {formatCurrency(payment.amount)}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {PAYMENT_METHODS.find(m => m.value === payment.payment_method)?.label || payment.payment_method}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-500">
                            {formatDate(payment.payment_date)}
                            {payment.reference && ` • Ref: ${payment.reference}`}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeletePayment(payment.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Notes */}
            {(invoice.memo || invoice.notes) && (
              <Card>
                <CardHeader>
                  <CardTitle>Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  {invoice.memo && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-500 mb-1">Client Memo</h4>
                      <p className="text-gray-900">{invoice.memo}</p>
                    </div>
                  )}
                  {invoice.notes && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 mb-1">Internal Notes</h4>
                      <p className="text-gray-900">{invoice.notes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Invoice Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-sm text-gray-500">Status</span>
                  <div className="mt-1">
                    <Badge className={STATUS_COLORS[invoice.status]}>{invoice.status}</Badge>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Payment Terms</span>
                  <p className="font-medium">{PAYMENT_TERMS_LABELS[invoice.payment_terms] || invoice.payment_terms}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Due Date</span>
                  <p className="font-medium">{formatDate(invoice.due_date)}</p>
                </div>
                {invoice.sent_at && (
                  <div>
                    <span className="text-sm text-gray-500">Sent</span>
                    <p className="font-medium">{formatDate(invoice.sent_at)}</p>
                  </div>
                )}
                {invoice.viewed_at && (
                  <div>
                    <span className="text-sm text-gray-500">Viewed</span>
                    <p className="font-medium">{formatDate(invoice.viewed_at)}</p>
                  </div>
                )}
                {invoice.paid_at && (
                  <div>
                    <span className="text-sm text-gray-500">Paid</span>
                    <p className="font-medium">{formatDate(invoice.paid_at)}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total</span>
                  <span className="font-medium">{formatCurrency(invoice.total)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Paid</span>
                  <span className="font-medium text-green-600">{formatCurrency(invoice.amount_paid)}</span>
                </div>
                <div className="border-t pt-3 flex justify-between">
                  <span className="font-medium">Balance Due</span>
                  <span className="font-bold text-lg">{formatCurrency(invoice.balance_due)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Record Payment</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    className="w-full rounded-md border border-gray-300 pl-7 pr-3 py-2"
                    step="0.01"
                    min="0.01"
                    max={invoice.balance_due}
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(e.target.value)}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Balance due: {formatCurrency(invoice.balance_due)}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2"
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                >
                  {PAYMENT_METHODS.map((method) => (
                    <option key={method.value} value={method.value}>
                      {method.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Date
                </label>
                <input
                  type="date"
                  className="w-full rounded-md border border-gray-300 px-3 py-2"
                  value={paymentDate}
                  onChange={(e) => setPaymentDate(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference (optional)
                </label>
                <input
                  type="text"
                  className="w-full rounded-md border border-gray-300 px-3 py-2"
                  placeholder="Check number, transaction ID, etc."
                  value={paymentReference}
                  onChange={(e) => setPaymentReference(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  className="w-full rounded-md border border-gray-300 px-3 py-2"
                  rows={2}
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="outline"
                onClick={() => setShowPaymentModal(false)}
                disabled={recordingPayment}
              >
                Cancel
              </Button>
              <Button onClick={handleRecordPayment} disabled={recordingPayment}>
                {recordingPayment ? "Recording..." : "Record Payment"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
}
