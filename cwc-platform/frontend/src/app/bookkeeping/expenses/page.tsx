"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { expensesApi, expenseCategoriesApi } from "@/lib/api";
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
import { Plus, Search, Pencil, Trash2, Receipt, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

interface Expense {
  id: string;
  description: string;
  amount: number;
  expense_date: string;
  category_id: string | null;
  category: { id: string; name: string; color: string } | null;
  vendor: string | null;
  payment_method: string;
  reference: string | null;
  is_tax_deductible: boolean;
  tax_year: number;
  notes: string | null;
}

interface Category {
  id: string;
  name: string;
  color: string;
  is_tax_deductible: boolean;
}

export default function ExpensesPage() {
  const { token } = useAuth();
  const currentYear = new Date().getFullYear();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [taxYear, setTaxYear] = useState(currentYear);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    description: "",
    amount: "",
    expense_date: new Date().toISOString().split("T")[0],
    category_id: "",
    vendor: "",
    payment_method: "card",
    reference: "",
    is_tax_deductible: true,
    notes: "",
  });

  useEffect(() => {
    if (token) {
      loadCategories();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      loadExpenses();
    }
  }, [token, page, search, categoryFilter, taxYear]);

  const loadCategories = async () => {
    if (!token) return;
    try {
      const data = await expenseCategoriesApi.list(token);
      setCategories(data);
    } catch (error) {
      console.error("Failed to load categories:", error);
    }
  };

  const loadExpenses = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await expensesApi.list(token, {
        page,
        size: 25,
        search: search || undefined,
        category_id: categoryFilter || undefined,
        tax_year: taxYear,
      });
      setExpenses(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to load expenses:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        category_id: formData.category_id || null,
      };

      if (editingExpense) {
        await expensesApi.update(token, editingExpense.id, data);
        toast.success("Expense updated");
      } else {
        await expensesApi.create(token, data);
        toast.success("Expense added");
      }

      setDialogOpen(false);
      resetForm();
      loadExpenses();
    } catch (error) {
      toast.error("Failed to save expense");
    }
  };

  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    setFormData({
      description: expense.description,
      amount: expense.amount.toString(),
      expense_date: expense.expense_date,
      category_id: expense.category_id || "",
      vendor: expense.vendor || "",
      payment_method: expense.payment_method,
      reference: expense.reference || "",
      is_tax_deductible: expense.is_tax_deductible,
      notes: expense.notes || "",
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!token || !confirm("Are you sure you want to delete this expense?")) return;
    try {
      await expensesApi.delete(token, id);
      toast.success("Expense deleted");
      loadExpenses();
    } catch (error) {
      toast.error("Failed to delete expense");
    }
  };

  const resetForm = () => {
    setEditingExpense(null);
    setFormData({
      description: "",
      amount: "",
      expense_date: new Date().toISOString().split("T")[0],
      category_id: "",
      vendor: "",
      payment_method: "card",
      reference: "",
      is_tax_deductible: true,
      notes: "",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
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
          <h1 className="text-3xl font-bold">Expenses</h1>
          <p className="text-muted-foreground">Track and manage business expenses</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Expense
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>{editingExpense ? "Edit Expense" : "Add Expense"}</DialogTitle>
                <DialogDescription>
                  {editingExpense ? "Update expense details" : "Record a new business expense"}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="description">Description *</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="What was this expense for?"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="amount">Amount *</Label>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="expense_date">Date *</Label>
                    <Input
                      id="expense_date"
                      type="date"
                      value={formData.expense_date}
                      onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="category">Category</Label>
                    <Select
                      value={formData.category_id}
                      onValueChange={(v) => setFormData({ ...formData, category_id: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {categories.map((cat) => (
                          <SelectItem key={cat.id} value={cat.id}>
                            {cat.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="vendor">Vendor</Label>
                    <Input
                      id="vendor"
                      value={formData.vendor}
                      onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                      placeholder="Company name"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="payment_method">Payment Method</Label>
                    <Select
                      value={formData.payment_method}
                      onValueChange={(v) => setFormData({ ...formData, payment_method: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="card">Credit/Debit Card</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="check">Check</SelectItem>
                        <SelectItem value="paypal">PayPal</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="reference">Reference #</Label>
                    <Input
                      id="reference"
                      value={formData.reference}
                      onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                      placeholder="Receipt or transaction #"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is_tax_deductible"
                    checked={formData.is_tax_deductible}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_tax_deductible: checked as boolean })}
                  />
                  <Label htmlFor="is_tax_deductible">Tax deductible expense</Label>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Additional details..."
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">{editingExpense ? "Update" : "Add"} Expense</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search expenses..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={categoryFilter} onValueChange={(v) => { setCategoryFilter(v); setPage(1); }}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={taxYear.toString()} onValueChange={(v) => { setTaxYear(parseInt(v)); setPage(1); }}>
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
          </div>
        </CardContent>
      </Card>

      {/* Expenses Table */}
      <Card>
        <CardHeader>
          <CardTitle>Expenses ({total})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : expenses.length === 0 ? (
            <div className="text-center py-8">
              <Receipt className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No expenses found</p>
              <Button className="mt-4" onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Expense
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Deductible</TableHead>
                    <TableHead className="w-20"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {expenses.map((expense) => (
                    <TableRow key={expense.id}>
                      <TableCell>
                        {new Date(expense.expense_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="font-medium">{expense.description}</TableCell>
                      <TableCell>
                        {expense.category ? (
                          <Badge
                            variant="outline"
                            style={{ borderColor: expense.category.color, color: expense.category.color }}
                          >
                            {expense.category.name}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>{expense.vendor || "—"}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(expense.amount)}
                      </TableCell>
                      <TableCell>
                        {expense.is_tax_deductible ? (
                          <Badge variant="default" className="bg-green-100 text-green-800">Yes</Badge>
                        ) : (
                          <Badge variant="secondary">No</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(expense)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(expense.id)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {total > 25 && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <span className="py-2 px-4 text-sm">
                    Page {page} of {Math.ceil(total / 25)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= Math.ceil(total / 25)}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
    </Shell>
  );
}
