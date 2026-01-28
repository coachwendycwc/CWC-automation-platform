"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { invoicesApi, contactsApi } from "@/lib/api";
import { Plus, Trash2, ArrowLeft, Save, Send } from "lucide-react";
import Link from "next/link";

interface Contact {
  id: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  organization_id: string | null;
}

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  service_type?: string;
}

const SERVICE_TYPES = [
  { value: "", label: "Select type..." },
  { value: "coaching", label: "Coaching" },
  { value: "workshop", label: "Workshop" },
  { value: "consulting", label: "Consulting" },
  { value: "keynote", label: "Keynote Speaking" },
  { value: "other", label: "Other" },
];

const PAYMENT_TERMS = [
  { value: "due_on_receipt", label: "Due on Receipt" },
  { value: "net_15", label: "Net 15" },
  { value: "net_30", label: "Net 30" },
  { value: "50_50_split", label: "50/50 Split" },
];

export default function NewInvoicePage() {
  const router = useRouter();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [contactId, setContactId] = useState<string>("");
  const [paymentTerms, setPaymentTerms] = useState<string>("net_30");
  const [taxRate, setTaxRate] = useState<string>("");
  const [discountAmount, setDiscountAmount] = useState<string>("0");
  const [memo, setMemo] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [lineItems, setLineItems] = useState<LineItem[]>([
    { description: "", quantity: 1, unit_price: 0 },
  ]);

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await contactsApi.list(token, { size: 100 });
      setContacts(response.items || []);
    } catch (err) {
      console.error("Failed to load contacts:", err);
    } finally {
      setLoading(false);
    }
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { description: "", quantity: 1, unit_price: 0 }]);
  };

  const removeLineItem = (index: number) => {
    if (lineItems.length > 1) {
      setLineItems(lineItems.filter((_, i) => i !== index));
    }
  };

  const updateLineItem = (index: number, field: keyof LineItem, value: any) => {
    const updated = [...lineItems];
    updated[index] = { ...updated[index], [field]: value };
    setLineItems(updated);
  };

  // Calculate totals
  const subtotal = lineItems.reduce((sum, item) => {
    return sum + (item.quantity * item.unit_price);
  }, 0);

  const taxAmount = taxRate ? subtotal * (parseFloat(taxRate) / 100) : 0;
  const discount = parseFloat(discountAmount) || 0;
  const total = subtotal + taxAmount - discount;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const handleSave = async (andSend: boolean = false) => {
    if (!contactId) {
      alert("Please select a contact");
      return;
    }

    if (lineItems.every(item => !item.description || item.unit_price === 0)) {
      alert("Please add at least one line item");
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const selectedContact = contacts.find(c => c.id === contactId);

      const data = {
        contact_id: contactId,
        organization_id: selectedContact?.organization_id || null,
        payment_terms: paymentTerms,
        tax_rate: taxRate ? parseFloat(taxRate) : null,
        discount_amount: discount,
        memo: memo || null,
        notes: notes || null,
        line_items: lineItems.filter(item => item.description && item.unit_price > 0),
      };

      const invoice = await invoicesApi.create(token, data);

      if (andSend) {
        await invoicesApi.send(token, invoice.id);
      }

      router.push(`/invoices/${invoice.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to create invoice");
    } finally {
      setSaving(false);
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
      <div className="space-y-6 max-w-4xl">
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
              <h1 className="text-2xl font-bold text-gray-900">New Invoice</h1>
              <p className="text-gray-600">Create a new invoice for your client</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => handleSave(false)} disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              Save Draft
            </Button>
            <Button onClick={() => handleSave(true)} disabled={saving}>
              <Send className="h-4 w-4 mr-2" />
              Save & Send
            </Button>
          </div>
        </div>

        {/* Client Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Client</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Contact *
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={contactId}
                  onChange={(e) => setContactId(e.target.value)}
                >
                  <option value="">Choose a contact...</option>
                  {contacts.map((contact) => (
                    <option key={contact.id} value={contact.id}>
                      {contact.first_name} {contact.last_name || ""} {contact.email ? `(${contact.email})` : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Terms
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                >
                  {PAYMENT_TERMS.map((term) => (
                    <option key={term.value} value={term.value}>
                      {term.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Line Items</CardTitle>
            <Button size="sm" variant="outline" onClick={addLineItem}>
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Header */}
              <div className="grid grid-cols-12 gap-2 text-xs font-medium text-gray-500 uppercase">
                <div className="col-span-5">Description</div>
                <div className="col-span-2">Service Type</div>
                <div className="col-span-1 text-center">Qty</div>
                <div className="col-span-2 text-right">Unit Price</div>
                <div className="col-span-1 text-right">Amount</div>
                <div className="col-span-1"></div>
              </div>

              {/* Items */}
              {lineItems.map((item, index) => (
                <div key={index} className="grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-5">
                    <input
                      type="text"
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      placeholder="Description"
                      value={item.description}
                      onChange={(e) => updateLineItem(index, "description", e.target.value)}
                    />
                  </div>
                  <div className="col-span-2">
                    <select
                      className="w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                      value={item.service_type || ""}
                      onChange={(e) => updateLineItem(index, "service_type", e.target.value)}
                    >
                      {SERVICE_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-1">
                    <input
                      type="number"
                      className="w-full rounded-md border border-gray-300 px-2 py-2 text-sm text-center"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateLineItem(index, "quantity", parseInt(e.target.value) || 1)}
                    />
                  </div>
                  <div className="col-span-2">
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                      <input
                        type="number"
                        className="w-full rounded-md border border-gray-300 pl-6 pr-2 py-2 text-sm text-right"
                        min="0"
                        step="0.01"
                        value={item.unit_price || ""}
                        onChange={(e) => updateLineItem(index, "unit_price", parseFloat(e.target.value) || 0)}
                      />
                    </div>
                  </div>
                  <div className="col-span-1 text-right text-sm font-medium">
                    {formatCurrency(item.quantity * item.unit_price)}
                  </div>
                  <div className="col-span-1 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeLineItem(index)}
                      disabled={lineItems.length === 1}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {/* Totals */}
            <div className="mt-6 border-t pt-4">
              <div className="flex justify-end">
                <div className="w-64 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Subtotal</span>
                    <span className="font-medium">{formatCurrency(subtotal)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Tax</span>
                      <input
                        type="number"
                        className="w-16 rounded-md border border-gray-300 px-2 py-1 text-sm text-right"
                        placeholder="%"
                        min="0"
                        max="100"
                        step="0.01"
                        value={taxRate}
                        onChange={(e) => setTaxRate(e.target.value)}
                      />
                      <span className="text-gray-500">%</span>
                    </div>
                    <span className="font-medium">{formatCurrency(taxAmount)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Discount</span>
                      <div className="relative">
                        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-xs">$</span>
                        <input
                          type="number"
                          className="w-20 rounded-md border border-gray-300 pl-5 pr-2 py-1 text-sm text-right"
                          min="0"
                          step="0.01"
                          value={discountAmount}
                          onChange={(e) => setDiscountAmount(e.target.value)}
                        />
                      </div>
                    </div>
                    <span className="font-medium text-red-500">-{formatCurrency(discount)}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>{formatCurrency(total)}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Memo (appears on invoice)
                </label>
                <textarea
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Thank you for your business..."
                  value={memo}
                  onChange={(e) => setMemo(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Internal Notes (not visible to client)
                </label>
                <textarea
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Notes for your reference..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
