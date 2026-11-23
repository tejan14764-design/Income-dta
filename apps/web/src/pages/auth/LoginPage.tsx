import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/authStore";
import { getApiBaseUrl, getErrorMessage, setApiBaseUrl } from "@/services/api";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [serverSettingsOpen, setServerSettingsOpen] = useState(false);
  const [serverUrl, setServerUrl] = useState(() => getApiBaseUrl());
  const [savingServerUrl, setSavingServerUrl] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    try {
      const response = await authService.login(data.username, data.password);
      login(response.user, response.memberships, response.access, response.refresh);

      if (response.user.must_change_password) {
        navigate("/change-password");
      } else {
        navigate("/dashboard");
      }
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const saveServerUrl = async () => {
    setSavingServerUrl(true);
    try {
      const normalized = await setApiBaseUrl(serverUrl);
      setServerUrl(normalized);
      setServerSettingsOpen(false);
      toast.success("Server URL updated.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Invalid server URL.");
    } finally {
      setSavingServerUrl(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-950 via-primary-900 to-primary-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center text-center mb-8">
          <img
            src={`${import.meta.env.BASE_URL}pre-school.jpeg`}
            alt="Bright Future Pre-School logo"
            className="h-20 w-20 rounded-2xl mb-4 object-cover"
          />
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-tight">
            BRIGHT FUTURE PRE-SCHOOL
          </h1>
          <p className="text-white/70 mt-2 text-sm sm:text-base">
            Where Little stars begin to shine
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-modal p-8">
          <h2 className="text-xl font-semibold text-text-primary mb-1">Welcome back</h2>
          <p className="text-sm text-text-secondary mb-6">Sign in to your account to continue</p>

          <div className="mb-4 flex justify-end">
            <button
              type="button"
              onClick={() => setServerSettingsOpen((v) => !v)}
              className="text-xs font-medium text-primary hover:underline"
            >
              Server settings
            </button>
          </div>

          {serverSettingsOpen && (
            <div className="mb-4 rounded-lg border border-surface-border bg-surface-muted p-3">
              <Input
                label="API Server URL"
                type="text"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="https://your-server.ngrok-free.dev/api/v1"
                helperText="Enter the backend API URL for this school server."
              />
              <div className="mt-3 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setServerUrl(getApiBaseUrl())}
                >
                  Reset
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  loading={savingServerUrl}
                  onClick={saveServerUrl}
                >
                  Save
                </Button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <Input
              label="Username or Email"
              type="text"
              autoComplete="username"
              autoFocus
              placeholder="Enter your username"
              error={errors.username?.message}
              {...register("username")}
            />

            <Input
              label="Password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="Enter your password"
              error={errors.password?.message}
              rightIcon={
                <button
                  type="button"
                  className="pointer-events-auto cursor-pointer"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              }
              {...register("password")}
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={isSubmitting}
              className="w-full mt-2"
            >
              Sign In
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-text-muted">
            Bright Future Pre-School v{import.meta.env.VITE_APP_VERSION ?? "1.0.0"} &copy; {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </div>
  );
}
