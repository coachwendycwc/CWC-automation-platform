"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { reportsApi } from "@/lib/api";
import { Shell } from "@/components/layout/Shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, TrendingUp, TrendingDown, DollarSign, Receipt, Car, Users, FileText, Calculator } from "lucide-react";
import Link from "next/link";

interface ProfitLossData {
  period_start: string;
  period_end: string;
  total_revenue: number;
  invoices_paid: number;
  total_expenses: number;
  expenses_by_category: Array<{ category: string; amount: number; count: number }>;
  total_mileage_deduction: number;
  total_contractor_payments: number;
  net_profit: number;
  profit_margin: number | null;
}

interface TaxSummaryData {
  tax_year: number;
  gross_income: number;
  total_expenses: number;
  mileage_deduction: number;
  contractor_payments: number;
  total_deductions: number;
  estimated_taxable_income: number;
  quarters: Array<{ quarter: number; income: number; expenses: number; mileage: number; net: number }>;
  contractors_needing_1099: Array<{
    contractor_id: string;
    contractor_name: string;
    total_paid: number;
    payment_count: number;
    needs_1099: boolean;
  }>;
}

export default function ReportsPage() {
  const { token } = useAuth();
  const currentYear = new Date().getFullYear();
  const [taxYear, setTaxYear] = useState(currentYear);
  const [profitLoss, setProfitLoss] = useState<ProfitLossData | null>(null);
  const [taxSummary, setTaxSummary] = useState<TaxSummaryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      loadReports();
    }
  }, [token, taxYear]);

  const loadReports = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [pl, tax] = await Promise.all([
        reportsApi.getProfitLoss(token, { tax_year: taxYear }),
        reportsApi.getTaxSummary(token, taxYear),
      ]);
      setProfitLoss(pl);
      setTaxSummary(tax);
    } catch (error) {
      console.error("Failed to load reports:", error);
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

  const quarterLabels = ["Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"];

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
          <h1 className="text-3xl font-bold">Financial Reports</h1>
          <p className="text-muted-foreground">Profit & Loss statements and tax summaries</p>
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
      </div>

      <Tabs defaultValue="pnl" className="space-y-6">
        <TabsList>
          <TabsTrigger value="pnl">Profit & Loss</TabsTrigger>
          <TabsTrigger value="tax">Tax Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="pnl" className="space-y-6">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : profitLoss ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      {formatCurrency(profitLoss.total_revenue)}
                    </div>
                    <p className="text-xs text-muted-foreground">{profitLoss.invoices_paid} invoices paid</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Expenses</CardTitle>
                    <Receipt className="h-4 w-4 text-red-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">
                      {formatCurrency(profitLoss.total_expenses)}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Mileage</CardTitle>
                    <Car className="h-4 w-4 text-blue-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(profitLoss.total_mileage_deduction)}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Net Profit</CardTitle>
                    {profitLoss.net_profit >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className={`text-2xl font-bold ${profitLoss.net_profit >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {formatCurrency(profitLoss.net_profit)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {profitLoss.profit_margin ? `${profitLoss.profit_margin.toFixed(1)}% margin` : "—"}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* P&L Statement */}
              <Card>
                <CardHeader>
                  <CardTitle>Profit & Loss Statement</CardTitle>
                  <CardDescription>
                    {new Date(profitLoss.period_start).toLocaleDateString()} - {new Date(profitLoss.period_end).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Revenue */}
                    <div className="border-b pb-4">
                      <h3 className="font-semibold text-lg mb-2">Revenue</h3>
                      <div className="flex justify-between py-1">
                        <span>Client Payments ({profitLoss.invoices_paid} invoices)</span>
                        <span className="font-medium">{formatCurrency(profitLoss.total_revenue)}</span>
                      </div>
                      <div className="flex justify-between py-1 font-semibold border-t mt-2 pt-2">
                        <span>Total Revenue</span>
                        <span className="text-green-600">{formatCurrency(profitLoss.total_revenue)}</span>
                      </div>
                    </div>

                    {/* Expenses */}
                    <div className="border-b pb-4">
                      <h3 className="font-semibold text-lg mb-2">Expenses</h3>
                      {profitLoss.expenses_by_category.map((cat) => (
                        <div key={cat.category} className="flex justify-between py-1">
                          <span>{cat.category} ({cat.count})</span>
                          <span>{formatCurrency(cat.amount)}</span>
                        </div>
                      ))}
                      <div className="flex justify-between py-1 font-semibold border-t mt-2 pt-2">
                        <span>Total Operating Expenses</span>
                        <span>{formatCurrency(profitLoss.total_expenses)}</span>
                      </div>
                    </div>

                    {/* Other Deductions */}
                    <div className="border-b pb-4">
                      <h3 className="font-semibold text-lg mb-2">Other Deductions</h3>
                      <div className="flex justify-between py-1">
                        <span>Business Mileage</span>
                        <span>{formatCurrency(profitLoss.total_mileage_deduction)}</span>
                      </div>
                      {profitLoss.total_contractor_payments > 0 && (
                        <div className="flex justify-between py-1">
                          <span>Contractor Payments (non-expense linked)</span>
                          <span>{formatCurrency(profitLoss.total_contractor_payments)}</span>
                        </div>
                      )}
                    </div>

                    {/* Net Profit */}
                    <div className="pt-2">
                      <div className="flex justify-between py-2 text-xl font-bold">
                        <span>Net Profit / (Loss)</span>
                        <span className={profitLoss.net_profit >= 0 ? "text-green-600" : "text-red-600"}>
                          {formatCurrency(profitLoss.net_profit)}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No data available</div>
          )}
        </TabsContent>

        <TabsContent value="tax" className="space-y-6">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : taxSummary ? (
            <>
              {/* Tax Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Gross Income</CardTitle>
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(taxSummary.gross_income)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Deductions</CardTitle>
                    <Receipt className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(taxSummary.total_deductions)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Est. Taxable Income</CardTitle>
                    <Calculator className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(taxSummary.estimated_taxable_income)}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Deduction Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Deduction Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between py-2 border-b">
                      <span>Business Expenses</span>
                      <span className="font-medium">{formatCurrency(taxSummary.total_expenses)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span>Mileage Deduction (IRS Standard Rate)</span>
                      <span className="font-medium">{formatCurrency(taxSummary.mileage_deduction)}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b text-muted-foreground">
                      <span className="text-sm">Contractor Payments (for reference, may be in expenses)</span>
                      <span className="text-sm">{formatCurrency(taxSummary.contractor_payments)}</span>
                    </div>
                    <div className="flex justify-between py-2 font-bold text-lg">
                      <span>Total Deductions</span>
                      <span>{formatCurrency(taxSummary.total_deductions)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quarterly Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Quarterly Summary</CardTitle>
                  <CardDescription>Estimated quarterly tax payments reference</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Quarter</TableHead>
                        <TableHead className="text-right">Income</TableHead>
                        <TableHead className="text-right">Expenses</TableHead>
                        <TableHead className="text-right">Mileage</TableHead>
                        <TableHead className="text-right">Net</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {taxSummary.quarters.map((q, i) => (
                        <TableRow key={q.quarter}>
                          <TableCell className="font-medium">{quarterLabels[i]}</TableCell>
                          <TableCell className="text-right">{formatCurrency(q.income)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(q.expenses)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(q.mileage)}</TableCell>
                          <TableCell className={`text-right font-medium ${q.net >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {formatCurrency(q.net)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {/* 1099 Contractors */}
              {taxSummary.contractors_needing_1099.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Contractors Requiring 1099-NEC
                    </CardTitle>
                    <CardDescription>
                      Contractors paid $600 or more in {taxYear} require a 1099-NEC form
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Contractor</TableHead>
                          <TableHead className="text-right">Total Paid</TableHead>
                          <TableHead className="text-right">Payments</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {taxSummary.contractors_needing_1099.map((c) => (
                          <TableRow key={c.contractor_id}>
                            <TableCell className="font-medium">{c.contractor_name}</TableCell>
                            <TableCell className="text-right">{formatCurrency(c.total_paid)}</TableCell>
                            <TableCell className="text-right">{c.payment_count}</TableCell>
                            <TableCell>
                              <Badge variant="default" className="bg-yellow-100 text-yellow-800">
                                1099 Required
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {/* Export Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Export for Tax Preparation</CardTitle>
                  <CardDescription>Download CSV files for your accountant or tax software</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-3">
                    <a href={reportsApi.exportExpensesCsv(taxYear)} download>
                      <Button variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        Expenses ({taxYear})
                      </Button>
                    </a>
                    <a href={reportsApi.exportMileageCsv(taxYear)} download>
                      <Button variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        Mileage Log ({taxYear})
                      </Button>
                    </a>
                    <a href={reportsApi.exportContractorsCsv(taxYear)} download>
                      <Button variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        1099 Report ({taxYear})
                      </Button>
                    </a>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No data available</div>
          )}
        </TabsContent>
      </Tabs>
    </div>
    </Shell>
  );
}
