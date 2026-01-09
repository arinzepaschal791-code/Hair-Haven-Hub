import { useState } from "react";
import { useLocation } from "wouter";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Lock, User, Eye, EyeOff } from "lucide-react";

export default function AdminLogin() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSetup, setIsSetup] = useState(false);

  const { data: session } = useQuery({
    queryKey: ["/api/admin/session"],
  });

  if (session?.isAdmin) {
    setLocation("/admin");
    return null;
  }

  const loginMutation = useMutation({
    mutationFn: async (data: { username: string; password: string }) => {
      const response = await apiRequest("POST", "/api/admin/login", data);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/session"] });
      toast({
        title: "Welcome back!",
        description: "Login successful. Redirecting to dashboard...",
      });
      setLocation("/admin");
    },
    onError: (error: any) => {
      toast({
        title: "Login failed",
        description: error.message || "Invalid username or password",
        variant: "destructive",
      });
    },
  });

  const setupMutation = useMutation({
    mutationFn: async (data: { password: string }) => {
      const response = await apiRequest("POST", "/api/admin/setup", data);
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Admin created!",
        description: "You can now log in with your credentials.",
      });
      setIsSetup(false);
    },
    onError: (error: any) => {
      if (error.message?.includes("already exists")) {
        setIsSetup(false);
      } else {
        toast({
          title: "Setup failed",
          description: error.message || "Failed to create admin account",
          variant: "destructive",
        });
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isSetup) {
      setupMutation.mutate({ password });
    } else {
      loginMutation.mutate({ username, password });
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Lock className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="font-serif text-2xl">
            {isSetup ? "Create Admin Account" : "Admin Login"}
          </CardTitle>
          <CardDescription>
            {isSetup
              ? "Set up your admin password to access the dashboard"
              : "Enter your credentials to access the admin dashboard"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isSetup && (
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-10"
                    placeholder="admin"
                    data-testid="input-username"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">
                {isSetup ? "Create Password" : "Password"}
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-10"
                  placeholder={isSetup ? "Choose a secure password" : "Enter your password"}
                  data-testid="input-password"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              {isSetup && (
                <p className="text-xs text-muted-foreground">
                  Password must be at least 6 characters
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending || setupMutation.isPending}
              data-testid="button-login"
            >
              {loginMutation.isPending || setupMutation.isPending
                ? "Please wait..."
                : isSetup
                ? "Create Admin Account"
                : "Login"}
            </Button>

            <div className="text-center">
              <Button
                type="button"
                variant="link"
                className="text-sm"
                onClick={() => setIsSetup(!isSetup)}
              >
                {isSetup
                  ? "Already have an account? Login"
                  : "First time? Create admin account"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
