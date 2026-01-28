"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { SignaturePad } from "@/components/contracts/SignaturePad";
import { publicContractApi } from "@/lib/api";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";

interface ContractPublic {
  contract_number: string;
  title: string;
  content: string;
  status: string;
  expires_at: string | null;
  is_expired: boolean;
  can_sign: boolean;
  contact_name: string;
  organization_name: string | null;
}

export default function SignContractPage() {
  const params = useParams();
  const token = params.token as string;

  const [contract, setContract] = useState<ContractPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [signerName, setSignerName] = useState("");
  const [signerEmail, setSignerEmail] = useState("");
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const [signatureType, setSignatureType] = useState<"drawn" | "typed">("drawn");
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  // Result state
  const [signed, setSigned] = useState(false);
  const [declined, setDeclined] = useState(false);

  useEffect(() => {
    if (token) {
      loadContract();
    }
  }, [token]);

  const loadContract = async () => {
    try {
      const data = await publicContractApi.get(token);
      setContract(data);
    } catch (err: any) {
      setError(err.message || "Failed to load contract");
    } finally {
      setLoading(false);
    }
  };

  const handleSign = async () => {
    if (!signatureData || !signerName || !signerEmail || !agreedToTerms) {
      alert("Please complete all required fields");
      return;
    }

    setSubmitting(true);
    try {
      await publicContractApi.sign(token, {
        signer_name: signerName,
        signer_email: signerEmail,
        signature_data: signatureData,
        signature_type: signatureType,
        agreed_to_terms: agreedToTerms,
      });
      setSigned(true);
    } catch (err: any) {
      alert(err.message || "Failed to sign contract");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecline = async () => {
    const reason = window.prompt("Please provide a reason for declining (optional):");
    if (reason === null) return; // cancelled

    setSubmitting(true);
    try {
      await publicContractApi.decline(token, reason);
      setDeclined(true);
    } catch (err: any) {
      alert(err.message || "Failed to decline contract");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignatureChange = (data: string | null, type: "drawn" | "typed") => {
    setSignatureData(data);
    setSignatureType(type);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading contract...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Contract Not Found</h2>
            <p className="text-gray-500">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!contract) {
    return null;
  }

  // Already signed
  if (contract.status === "signed" || signed) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Contract Signed!</h2>
            <p className="text-gray-500 mb-4">
              Thank you for signing. A confirmation email will be sent to you shortly.
            </p>
            <p className="text-sm text-gray-400">
              Contract: {contract.contract_number}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Declined
  if (contract.status === "declined" || declined) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <XCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Contract Declined</h2>
            <p className="text-gray-500 mb-4">
              This contract has been declined. Please contact us if you have any questions.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Expired
  if (contract.is_expired || contract.status === "expired") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <Clock className="h-16 w-16 text-orange-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Contract Expired</h2>
            <p className="text-gray-500 mb-4">
              This contract has expired. Please contact us for a new contract.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Void
  if (contract.status === "void") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md w-full mx-4">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Contract Cancelled</h2>
            <p className="text-gray-500 mb-4">
              This contract has been cancelled. Please contact us for more information.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Can sign - show signing form
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 space-y-6">
        {/* Header */}
        <div className="text-center">
          <Image
            src="/images/logo.png"
            alt="Coaching Women of Color"
            width={200}
            height={170}
            className="h-20 w-auto mx-auto mb-4"
          />
          <h1 className="text-2xl font-bold">{contract.title}</h1>
          <p className="text-gray-500">
            Contract for {contract.contact_name}
            {contract.organization_name && ` (${contract.organization_name})`}
          </p>
          {contract.expires_at && (
            <p className="text-sm text-orange-600 mt-2">
              Please sign by{" "}
              {new Date(contract.expires_at).toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </p>
          )}
        </div>

        {/* Contract Content */}
        <Card>
          <CardHeader>
            <CardTitle>Contract Terms</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="prose max-w-none bg-white border rounded-lg p-6"
              dangerouslySetInnerHTML={{ __html: contract.content }}
            />
          </CardContent>
        </Card>

        {/* Signature Section */}
        <Card>
          <CardHeader>
            <CardTitle>Your Signature</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Signer Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Your Full Legal Name *</Label>
                <Input
                  value={signerName}
                  onChange={(e) => setSignerName(e.target.value)}
                  placeholder="Enter your full name"
                  required
                />
              </div>
              <div>
                <Label>Your Email *</Label>
                <Input
                  type="email"
                  value={signerEmail}
                  onChange={(e) => setSignerEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            {/* Signature Pad */}
            <div>
              <Label className="mb-2 block">Your Signature *</Label>
              <SignaturePad onSignatureChange={handleSignatureChange} />
            </div>

            {/* Agreement */}
            <div className="flex items-start space-x-3 pt-4 border-t">
              <Checkbox
                id="terms"
                checked={agreedToTerms}
                onCheckedChange={(checked) => setAgreedToTerms(checked as boolean)}
              />
              <label htmlFor="terms" className="text-sm text-gray-600 leading-relaxed">
                I have read and agree to the terms of this contract. I understand that
                by signing electronically, I am creating a legally binding agreement.
              </label>
            </div>

            {/* Actions */}
            <div className="flex justify-between pt-4">
              <Button
                variant="outline"
                onClick={handleDecline}
                disabled={submitting}
              >
                Decline Contract
              </Button>
              <Button
                onClick={handleSign}
                disabled={
                  !signatureData ||
                  !signerName ||
                  !signerEmail ||
                  !agreedToTerms ||
                  submitting
                }
              >
                {submitting ? "Signing..." : "Sign Contract"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 py-4">
          <p>Contract #{contract.contract_number}</p>
          <p className="mt-1">
            Coaching Women of Color | Electronic signatures are legally binding
          </p>
        </div>
      </div>
    </div>
  );
}
