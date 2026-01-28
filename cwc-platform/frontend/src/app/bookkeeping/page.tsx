"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { expensesApi, mileageApi, contractorsApi, reportsApi } from "@/lib/api";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DollarSign, Car, Users, FileText, TrendingUp, TrendingDown, Receipt, Download } from "lucide-react";
import Link from "next/link";

interface BookkeepingSummary {
  totalExpenses: number;
  totalDeductible: number;
  totalMiles: number;
  mileageDeduction: number;
  contractorsTotal: number;
  contractorsNeeding1099: number;
  netProfit: number;
  profitMargin: number | null;
}

export default function BookkeepingPage() {
  const { token } = useAuth();
  const currentYear = new Date().getFullYear();
  const [taxYear, setTaxYear] = useState(currentYear);
  const [summary, setSummary] = useState<BookkeepingSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      loadSummary();
    }
  }, [token, taxYear]);

  const loadSummary = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [expenseSummary, mileageSummary, contractors1099, profitLoss] = await Promise.all([
        expensesApi.getSummary(token, taxYear),
        mileageApi.getSummary(token, taxYear),
        contractorsApi.get1099Summary(token, taxYear),
        reportsApi.getProfitLoss(token, { tax_year: taxYear }),
      ]);

      setSummary({
        totalExpenses: expenseSummary.total_expenses,
        totalDeductible: expenseSummary.total_deductible,
        totalMiles: mileageSummary.total_miles,
        mileageDeduction: mileageSummary.total_deduction,
        contractorsTotal: contractors1099.reduce((sum: number, c: any) => sum + c.total_paid, 0),
        contractorsNeeding1099: contractors1099.filter((c: any) => c.needs_1099).length,
        netProfit: profitLoss.net_profit,
        profitMargin: profitLoss.profit_margin,
      });
    } catch (error) {
      console.error("Failed to load bookkeeping summary:", error);
    } finally {
      setLoading(false);
    }
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Bookkeeping</h1>
          <p className="text-muted-foreground">Track expenses, mileage, contractors, and tax reports</p>
        </div>
        <div className="flex items-center gap-4">
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
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <Receipt className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : formatCurrency(summary?.totalExpenses || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {loading ? "" : `${formatCurrency(summary?.totalDeductible || 0)} deductible`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mileage Deduction</CardTitle>
            <Car className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : formatCurrency(summary?.mileageDeduction || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {loading ? "" : `${(summary?.totalMiles || 0).toLocaleString()} miles logged`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contractor Payments</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? "..." : formatCurrency(summary?.contractorsTotal || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {loading ? "" : `${summary?.contractorsNeeding1099 || 0} contractors need 1099`}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
            {(summary?.netProfit || 0) >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(summary?.netProfit || 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
              {loading ? "..." : formatCurrency(summary?.netProfit || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {loading ? "" : summary?.profitMargin ? `${summary.profitMargin.toFixed(1)}% margin` : "No revenue yet"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link href="/bookkeeping/expenses">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5" />
                Expenses
              </CardTitle>
              <CardDescription>Track business expenses and subscriptions</CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/bookkeeping/mileage">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Car className="h-5 w-5" />
                Mileage
              </CardTitle>
              <CardDescription>Log business trips for tax deductions</CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/bookkeeping/contractors">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Contractors
              </CardTitle>
              <CardDescription>Manage 1099 contractors and payments</CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/bookkeeping/reports">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Tax Reports
              </CardTitle>
              <CardDescription>P&L statements and tax summaries</CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>

      {/* Export Section */}
      <Card>
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
          <CardDescription>Download CSV files for your records or accountant</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <a href={reportsApi.exportExpensesCsv(taxYear)} download>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Expenses CSV
              </Button>
            </a>
            <a href={reportsApi.exportMileageCsv(taxYear)} download>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Mileage Log CSV
              </Button>
            </a>
            <a href={reportsApi.exportContractorsCsv(taxYear)} download>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                1099 Contractors CSV
              </Button>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
    </Shell>
  );
}
