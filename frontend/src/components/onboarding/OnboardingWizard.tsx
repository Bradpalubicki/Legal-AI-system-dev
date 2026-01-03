"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Clock,
  Play,
  FileText,
  Users,
  Settings,
  MapPin,
  Bell,
  Upload,
  BookOpen,
  Award,
  SkipForward
} from "lucide-react";
import { cn } from "@/lib/utils";

interface OnboardingWizardProps {
  userId: string;
  onComplete?: () => void;
}

interface StepData {
  step: string;
  title: string;
  description: string;
  content: any;
  estimated_time: number;
  required: boolean;
}

interface SessionData {
  session_id: string;
  current_step: string;
  completion_percentage: number;
  profile: any;
}

const stepIcons = {
  welcome: Play,
  account_setup: Users,
  role_selection: Users,
  firm_profile: FileText,
  practice_areas: BookOpen,
  state_selection: MapPin,
  communication_preferences: Bell,
  first_document: Upload,
  sample_analysis: FileText,
  feature_tour: Settings,
  completion: Award
};

export function OnboardingWizard({ userId, onComplete }: OnboardingWizardProps) {
  const [session, setSession] = useState<SessionData | null>(null);
  const [currentStepData, setCurrentStepData] = useState<StepData | null>(null);
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    startOnboarding();
  }, [userId]);

  const startOnboarding = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/onboarding/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });

      if (!response.ok) throw new Error('Failed to start onboarding');

      const data = await response.json();
      setSession(data);
      await loadCurrentStep(data.current_step);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentStep = async (stepName: string) => {
    try {
      const response = await fetch(`/api/onboarding/step/${stepName}`);
      if (!response.ok) throw new Error('Failed to load step');

      const stepData = await response.json();
      setCurrentStepData(stepData);
      setFormData({});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load step');
    }
  };

  const completeStep = async (data: any) => {
    if (!session) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/onboarding/session/${session.session_id}/complete-step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step: currentStepData?.step,
          data
        })
      });

      if (!response.ok) throw new Error('Failed to complete step');

      const result = await response.json();
      setSession(prev => prev ? { ...prev, ...result } : null);

      if (result.current_step) {
        await loadCurrentStep(result.current_step);
      } else {
        onComplete?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete step');
    } finally {
      setLoading(false);
    }
  };

  const skipStep = async (reason: string = "User chose to skip") => {
    if (!session || !currentStepData) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/onboarding/session/${session.session_id}/skip-step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step: currentStepData.step,
          reason
        })
      });

      if (!response.ok) throw new Error('Failed to skip step');

      const result = await response.json();
      setSession(prev => prev ? { ...prev, ...result } : null);

      if (result.current_step) {
        await loadCurrentStep(result.current_step);
      } else {
        onComplete?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to skip step');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    if (!currentStepData) return null;

    switch (currentStepData.step) {
      case 'welcome':
        return <WelcomeStep data={currentStepData} onNext={() => completeStep({})} />;

      case 'role_selection':
        return (
          <RoleSelectionStep
            data={currentStepData}
            onNext={(data) => completeStep(data)}
          />
        );

      case 'practice_areas':
        return (
          <PracticeAreasStep
            data={currentStepData}
            onNext={(data) => completeStep(data)}
          />
        );

      case 'firm_profile':
        return (
          <FirmProfileStep
            data={currentStepData}
            onNext={(data) => completeStep(data)}
            onSkip={() => skipStep("User chose to skip firm profile")}
          />
        );

      case 'state_selection':
        return (
          <StateSelectionStep
            data={currentStepData}
            onNext={(data) => completeStep(data)}
          />
        );

      case 'communication_preferences':
        return (
          <CommunicationPreferencesStep
            data={currentStepData}
            onNext={(data) => completeStep(data)}
            onSkip={() => skipStep("User chose to skip preferences")}
          />
        );

      case 'completion':
        return <CompletionStep data={currentStepData} onComplete={onComplete} />;

      default:
        return <GenericStep data={currentStepData} onNext={(data) => completeStep(data)} />;
    }
  };

  if (loading && !session) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="p-6">
          <div className="text-center">Loading onboarding...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>Error: {error}</p>
            <Button onClick={startOnboarding} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const Icon = currentStepData ? stepIcons[currentStepData.step as keyof typeof stepIcons] || Settings : Settings;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Icon className="h-6 w-6 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Legal AI System Setup</h1>
                <p className="text-muted-foreground">
                  Get your personalized legal assistant ready
                </p>
              </div>
            </div>
            <Badge variant="secondary">
              {session?.completion_percentage.toFixed(0)}% Complete
            </Badge>
          </div>
          <Progress value={session?.completion_percentage || 0} className="h-2" />
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {currentStepData?.title}
                {currentStepData?.estimated_time && (
                  <Badge variant="outline" className="ml-2">
                    <Clock className="h-3 w-3 mr-1" />
                    {currentStepData.estimated_time} min
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>{currentStepData?.description}</CardDescription>
            </div>
            {currentStepData && !currentStepData.required && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => skipStep()}
                className="text-muted-foreground hover:text-foreground"
              >
                <SkipForward className="h-4 w-4 mr-1" />
                Skip
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {renderStepContent()}
        </CardContent>
      </Card>
    </div>
  );
}

// Step Components
function WelcomeStep({ data, onNext }: { data: StepData; onNext: () => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold mb-4">Welcome to Legal AI System</h2>
        <p className="text-lg text-muted-foreground mb-6">
          {data.content.welcome_message}
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {data.content.benefits?.map((benefit: string, index: number) => (
          <div key={index} className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
            <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
            <span>{benefit}</span>
          </div>
        ))}
      </div>

      {data.content.video_url && (
        <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
          <Play className="h-12 w-12 text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Introduction Video</span>
        </div>
      )}

      <div className="text-center">
        <Button onClick={onNext} size="lg">
          Get Started
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function RoleSelectionStep({ data, onNext }: { data: StepData; onNext: (data: any) => void }) {
  const [selectedRole, setSelectedRole] = useState("");

  return (
    <div className="space-y-6">
      <RadioGroup value={selectedRole} onValueChange={setSelectedRole}>
        <div className="grid gap-4">
          {data.content.roles?.map((role: any) => (
            <div key={role.value} className="relative">
              <RadioGroupItem
                value={role.value}
                id={role.value}
                className="peer sr-only"
              />
              <Label
                htmlFor={role.value}
                className={cn(
                  "flex flex-col p-6 rounded-lg border-2 cursor-pointer transition-all",
                  "peer-checked:border-primary peer-checked:bg-primary/5",
                  "hover:border-primary/50"
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">{role.label}</h3>
                  <CheckCircle className="h-5 w-5 text-primary opacity-0 peer-checked:opacity-100" />
                </div>
                <p className="text-muted-foreground mb-4">{role.description}</p>
                <div className="grid grid-cols-2 gap-2">
                  {role.features?.slice(0, 4).map((feature: string, index: number) => (
                    <div key={index} className="text-sm text-muted-foreground">
                      • {feature}
                    </div>
                  ))}
                </div>
              </Label>
            </div>
          ))}
        </div>
      </RadioGroup>

      <div className="text-center">
        <Button
          onClick={() => onNext({ role: selectedRole })}
          disabled={!selectedRole}
          size="lg"
        >
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function PracticeAreasStep({ data, onNext }: { data: StepData; onNext: (data: any) => void }) {
  const [selectedAreas, setSelectedAreas] = useState<string[]>([]);

  const toggleArea = (area: string) => {
    setSelectedAreas(prev =>
      prev.includes(area)
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-muted-foreground">
          Select up to {data.content.max_selections} practice areas that best describe your work
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {data.content.areas?.map((area: any) => (
          <div
            key={area.value}
            className={cn(
              "p-4 rounded-lg border-2 cursor-pointer transition-all",
              selectedAreas.includes(area.value)
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            )}
            onClick={() => toggleArea(area.value)}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">{area.label}</h3>
              <Checkbox
                checked={selectedAreas.includes(area.value)}
                onChange={() => {}}
                className="pointer-events-none"
              />
            </div>
            <p className="text-sm text-muted-foreground">{area.description}</p>
          </div>
        ))}
      </div>

      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-4">
          Selected: {selectedAreas.length} / {data.content.max_selections}
        </p>
        <Button
          onClick={() => onNext({ practice_areas: selectedAreas })}
          disabled={selectedAreas.length === 0}
          size="lg"
        >
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function FirmProfileStep({ data, onNext, onSkip }: { data: StepData; onNext: (data: any) => void; onSkip: () => void }) {
  const [formData, setFormData] = useState<any>({});

  return (
    <div className="space-y-6">
      <div className="grid gap-6">
        {data.content.fields?.map((field: any) => (
          <div key={field.name} className="space-y-2">
            <Label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            {field.type === 'select' ? (
              <Select
                value={formData[field.name] || ""}
                onValueChange={(value) => setFormData(prev => ({ ...prev, [field.name]: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder={`Select ${field.label}`} />
                </SelectTrigger>
                <SelectContent>
                  {field.options?.map((option: string) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                id={field.name}
                type={field.type}
                placeholder={field.label}
                value={formData[field.name] || ""}
                onChange={(e) => setFormData(prev => ({ ...prev, [field.name]: e.target.value }))}
                required={field.required}
              />
            )}
          </div>
        ))}
      </div>

      <div className="flex justify-between">
        <Button variant="ghost" onClick={onSkip}>
          Skip for now
        </Button>
        <Button onClick={() => onNext(formData)} size="lg">
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function StateSelectionStep({ data, onNext }: { data: StepData; onNext: (data: any) => void }) {
  const [selectedState, setSelectedState] = useState("");

  return (
    <div className="space-y-6">
      <Select value={selectedState} onValueChange={setSelectedState}>
        <SelectTrigger>
          <SelectValue placeholder="Select your primary jurisdiction" />
        </SelectTrigger>
        <SelectContent>
          {data.content.options?.map((state: string) => (
            <SelectItem key={state} value={state}>
              {state}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="text-center">
        <Button
          onClick={() => onNext({ state: selectedState })}
          disabled={!selectedState}
          size="lg"
        >
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function CommunicationPreferencesStep({
  data,
  onNext,
  onSkip
}: {
  data: StepData;
  onNext: (data: any) => void;
  onSkip: () => void;
}) {
  const [preferences, setPreferences] = useState<any>({});

  const updatePreference = (category: string, key: string, value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  return (
    <div className="space-y-6">
      {data.content.preferences?.map((category: any) => (
        <div key={category.category} className="space-y-4">
          <h3 className="font-semibold text-lg">{category.category}</h3>
          <div className="space-y-3">
            {category.options?.map((option: any) => (
              <div key={option.key} className="flex items-center space-x-2">
                <Checkbox
                  id={option.key}
                  checked={preferences[category.category]?.[option.key] ?? option.default}
                  onCheckedChange={(checked) =>
                    updatePreference(category.category, option.key, checked as boolean)
                  }
                />
                <Label htmlFor={option.key} className="font-normal">
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex justify-between">
        <Button variant="ghost" onClick={onSkip}>
          Use defaults
        </Button>
        <Button onClick={() => onNext({ preferences })} size="lg">
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

function CompletionStep({ data, onComplete }: { data: StepData; onComplete?: () => void }) {
  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
        <Award className="h-8 w-8 text-green-600" />
      </div>

      <div>
        <h2 className="text-3xl font-bold mb-4">Setup Complete!</h2>
        <p className="text-lg text-muted-foreground mb-6">
          {data.content.completion_message}
        </p>
      </div>

      <div className="text-left max-w-2xl mx-auto">
        <h3 className="font-semibold mb-3">Next Steps:</h3>
        <div className="space-y-2">
          {data.content.next_steps?.map((step: string, index: number) => (
            <div key={index} className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm">{step}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4 max-w-2xl mx-auto">
        {data.content.resources?.map((resource: any, index: number) => (
          <Card key={index} className="text-left">
            <CardContent className="p-4">
              <h4 className="font-semibold mb-2">{resource.title}</h4>
              <p className="text-sm text-muted-foreground mb-3">{resource.description}</p>
              <Button variant="outline" size="sm" asChild>
                <a href={resource.url}>Learn More</a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {data.content.certificate?.downloadable && (
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6">
            <div className="text-center">
              <Award className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
              <h3 className="font-semibold mb-2">{data.content.certificate.title}</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {data.content.certificate.description}
              </p>
              <Button variant="outline">
                Download Certificate
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="pt-6">
        <Button onClick={onComplete} size="lg">
          Start Using Legal AI System
        </Button>
      </div>
    </div>
  );
}

function GenericStep({ data, onNext }: { data: StepData; onNext: (data: any) => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-muted-foreground">
          This step is not yet implemented. Click continue to proceed.
        </p>
      </div>

      <div className="text-center">
        <Button onClick={() => onNext({})} size="lg">
          Continue
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}