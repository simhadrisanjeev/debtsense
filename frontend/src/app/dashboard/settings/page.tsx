"use client";

import { useState } from "react";
import { Card, CardHeader, CardBody, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  User,
  Lock,
  Bell,
  AlertTriangle,
  Mail,
  Smartphone,
  FileText,
} from "lucide-react";
import { getStoredUser } from "@/lib/auth";

function Toggle({
  label,
  description,
  icon: Icon,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  icon: React.ElementType;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100">
          <Icon className="h-4 w-4 text-gray-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
          checked ? "bg-primary-600" : "bg-gray-200"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const storedUser = getStoredUser();

  // Profile state — seeded from localStorage
  const [firstName, setFirstName] = useState(storedUser?.first_name ?? "");
  const [lastName, setLastName] = useState(storedUser?.last_name ?? "");
  const [email, setEmail] = useState(storedUser?.email ?? "");

  // Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Notification state
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);
  const [monthlyReports, setMonthlyReports] = useState(true);

  // Form state
  const [profileSaving, setProfileSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

  const handleProfileSave = () => {
    setProfileSaving(true);
    setTimeout(() => setProfileSaving(false), 1000);
  };

  const handlePasswordUpdate = () => {
    setPasswordSaving(true);
    setTimeout(() => {
      setPasswordSaving(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }, 1000);
  };

  const passwordError =
    confirmPassword && newPassword !== confirmPassword
      ? "Passwords do not match"
      : undefined;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account preferences
        </p>
      </div>

      {/* Profile Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-100">
              <User className="h-4 w-4 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
              <p className="text-sm text-gray-500">
                Update your personal information
              </p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="First Name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="First name"
              />
              <Input
                label="Last Name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Last name"
              />
            </div>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              leftIcon={<Mail className="h-4 w-4" />}
            />
          </div>
        </CardBody>
        <CardFooter>
          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={handleProfileSave}
              loading={profileSaving}
            >
              Save Changes
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Password Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-warning-100">
              <Lock className="h-4 w-4 text-warning-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Password</h2>
              <p className="text-sm text-gray-500">
                Update your password to keep your account secure
              </p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              leftIcon={<Lock className="h-4 w-4" />}
            />
            <Input
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              leftIcon={<Lock className="h-4 w-4" />}
              helperText="Must be at least 8 characters with a number and special character"
            />
            <Input
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              leftIcon={<Lock className="h-4 w-4" />}
              error={passwordError}
            />
          </div>
        </CardBody>
        <CardFooter>
          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={handlePasswordUpdate}
              loading={passwordSaving}
              disabled={
                !currentPassword ||
                !newPassword ||
                !confirmPassword ||
                !!passwordError
              }
            >
              Update Password
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Notifications Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success-100">
              <Bell className="h-4 w-4 text-success-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Notifications
              </h2>
              <p className="text-sm text-gray-500">
                Choose how you want to be notified
              </p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="divide-y divide-gray-100">
            <Toggle
              label="Email Notifications"
              description="Receive payment reminders and updates via email"
              icon={Mail}
              checked={emailNotifications}
              onChange={setEmailNotifications}
            />
            <Toggle
              label="Push Notifications"
              description="Get real-time alerts on your device"
              icon={Smartphone}
              checked={pushNotifications}
              onChange={setPushNotifications}
            />
            <Toggle
              label="Monthly Reports"
              description="Receive a monthly summary of your debt payoff progress"
              icon={FileText}
              checked={monthlyReports}
              onChange={setMonthlyReports}
            />
          </div>
        </CardBody>
      </Card>

      {/* Danger Zone */}
      <Card className="border-danger-200">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-danger-100">
              <AlertTriangle className="h-4 w-4 text-danger-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-danger-600">
                Danger Zone
              </h2>
              <p className="text-sm text-gray-500">
                Irreversible and destructive actions
              </p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">
                Delete Account
              </p>
              <p className="text-sm text-gray-500">
                Permanently delete your account and all associated data. This
                action cannot be undone.
              </p>
            </div>
            <Button variant="danger" size="sm">
              Delete Account
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
