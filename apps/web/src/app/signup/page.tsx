"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Zap, Mail, Lock, User, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await api.post("/v1/auth/sign-up", { 
        email, 
        password, 
        name 
      });
      setIsSuccess(true);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6 relative overflow-hidden dark">
      {/* Decorative background */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 blur-[120px]" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="text-center mb-8">
          <div className="inline-flex w-12 h-12 rounded-2xl premium-gradient items-center justify-center mb-4 shadow-xl shadow-primary/20">
            <Zap className="text-white w-6 h-6" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Create Account</h1>
          <p className="text-muted-foreground mt-2">Start managing your fleet for free</p>
        </div>

        <div className="bg-card border glass-dark p-8 rounded-3xl shadow-2xl relative overflow-hidden">
          <AnimatePresence mode="wait">
            {!isSuccess ? (
              <motion.form 
                key="form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, x: -20 }}
                onSubmit={handleSubmit} 
                className="space-y-5"
              >
                <div className="space-y-2">
                  <label className="text-sm font-medium ml-1">Full Name</label>
                  <div className="relative group">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <input 
                      type="text" 
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="John Doe"
                      required
                      className="w-full pl-11 pr-4 py-3 rounded-2xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium ml-1">Email Address</label>
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <input 
                      type="email" 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      required
                      className="w-full pl-11 pr-4 py-3 rounded-2xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium ml-1">Password</label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <input 
                      type="password" 
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 8 characters"
                      required
                      minLength={8}
                      className="w-full pl-11 pr-4 py-3 rounded-2xl bg-secondary/50 border border-transparent focus:border-primary/30 focus:bg-secondary transition-all outline-none"
                    />
                  </div>
                </div>

                {error && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium"
                  >
                    {error}
                  </motion.div>
                )}

                <button 
                  type="submit" 
                  disabled={isLoading}
                  className="w-full py-4 px-6 rounded-2xl premium-gradient text-white font-bold shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all flex items-center justify-center gap-2 group disabled:opacity-70"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      Create Account
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </motion.form>
            ) : (
              <motion.div 
                key="success"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-center py-8"
              >
                <div className="inline-flex w-16 h-16 rounded-full bg-emerald-500/20 items-center justify-center mb-6">
                  <CheckCircle2 className="text-emerald-500 w-8 h-8" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Check your email</h2>
                <p className="text-muted-foreground mb-8">We&apos;ve sent a verification link to <span className="text-foreground font-medium">{email}</span></p>
                <button 
                  onClick={() => router.push("/login")}
                  className="w-full py-3 px-6 rounded-2xl bg-secondary hover:bg-secondary/80 font-bold transition-all"
                >
                  Back to Login
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-8 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <a href="/login" className="text-primary font-bold hover:underline">Sign In</a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
