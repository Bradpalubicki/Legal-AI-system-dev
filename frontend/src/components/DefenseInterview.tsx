'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, ArrowRight, ArrowLeft, Info, AlertTriangle } from 'lucide-react';

interface Question {
  id: string;
  text: string;
  type: 'text' | 'currency' | 'date' | 'yes_no' | 'choice' | 'textarea' | 'email';
  options?: string[];
  required?: boolean;
  hint?: string;
  validation?: (value: string) => string | null;
}

interface DefenseInterviewProps {
  caseType: string;
  onComplete: (defenseStrategy: any) => void;
  initialMessage?: string;
}

const questionsByType: Record<string, Question[]> = {
  bankruptcy: [
    {
      id: 'debt_amount',
      text: 'What is your approximate total debt amount?',
      type: 'currency',
      required: true,
      hint: 'Include all debts: credit cards, loans, medical bills, etc.',
      validation: (value) => {
        const amount = parseFloat(value.replace(/[$,]/g, ''));
        if (isNaN(amount) || amount < 0) return 'Please enter a valid amount';
        return null;
      }
    },
    {
      id: 'debt_type',
      text: 'Is this primarily business debt, personal debt, or both?',
      type: 'choice',
      options: ['Personal debt only', 'Business debt only', 'Both personal and business'],
      required: true,
      hint: 'This affects which bankruptcy chapter you may qualify for'
    },
    {
      id: 'last_payment',
      text: 'When did you last make a payment on this debt?',
      type: 'date',
      required: true,
      hint: 'This helps determine statute of limitations defenses'
    },
    {
      id: 'lawsuits',
      text: 'Have any creditors filed lawsuits against you?',
      type: 'yes_no',
      required: true
    },
    {
      id: 'assets',
      text: 'List your major assets (home, car, savings, investments):',
      type: 'textarea',
      required: true,
      hint: 'This helps determine what property may be protected in bankruptcy'
    },
    {
      id: 'income',
      text: 'What is your current monthly income?',
      type: 'currency',
      required: true,
      hint: 'Include all sources: job, benefits, rental income, etc.'
    }
  ],
  'debt collection': [
    {
      id: 'debt_age',
      text: 'How old is this debt? When was it incurred?',
      type: 'date',
      required: true,
      hint: 'Older debts may be past the statute of limitations'
    },
    {
      id: 'original_creditor',
      text: 'Who was the original creditor?',
      type: 'text',
      required: true,
      hint: 'Bank name, store, credit card company, etc.'
    },
    {
      id: 'debt_verified',
      text: 'Have you requested debt verification from the collector?',
      type: 'yes_no',
      required: true,
      hint: 'You have the right to request proof that you owe this debt'
    },
    {
      id: 'payment_history',
      text: 'When did you last make a payment on this account?',
      type: 'date',
      required: true,
      hint: 'This affects statute of limitations calculations'
    },
    {
      id: 'collection_violations',
      text: 'Has the collector violated any rules? (Called before 8am/after 9pm, threatened illegal action, etc.)',
      type: 'textarea',
      required: false,
      hint: 'FDCPA violations can be used as counterclaims'
    },
    {
      id: 'debt_amount_disputed',
      text: 'Do you dispute the amount they claim you owe?',
      type: 'yes_no',
      required: true
    }
  ],
  eviction: [
    {
      id: 'lease_type',
      text: 'What type of lease do you have?',
      type: 'choice',
      options: ['Written lease', 'Oral/verbal agreement', 'Month-to-month', 'No formal agreement'],
      required: true
    },
    {
      id: 'rent_behind',
      text: 'How much rent are you behind, if any?',
      type: 'currency',
      required: true,
      hint: 'Enter 0 if you are current on rent'
    },
    {
      id: 'notice_received',
      text: 'What type of notice did you receive from the landlord?',
      type: 'choice',
      options: ['Pay or Quit notice', 'Cure or Quit notice', 'Unconditional Quit notice', 'No notice received', 'Other'],
      required: true
    },
    {
      id: 'notice_date',
      text: 'When did you receive the notice?',
      type: 'date',
      required: true,
      hint: 'This affects timing requirements for your response'
    },
    {
      id: 'habitability_issues',
      text: 'Are there any habitability problems with the rental unit?',
      type: 'textarea',
      required: false,
      hint: 'Mold, heating issues, plumbing problems, pest infestations, etc.'
    },
    {
      id: 'discrimination',
      text: 'Do you believe this eviction is based on discrimination or retaliation?',
      type: 'yes_no',
      required: true
    }
  ],
  criminal: [
    {
      id: 'charge_type',
      text: 'What type of charges are you facing?',
      type: 'choice',
      options: ['Misdemeanor', 'Felony', 'Traffic violation', 'Municipal ordinance', 'Multiple charges'],
      required: true
    },
    {
      id: 'arrest_date',
      text: 'When were you arrested or cited?',
      type: 'date',
      required: true
    },
    {
      id: 'miranda_rights',
      text: 'Were you read your Miranda rights before questioning?',
      type: 'choice',
      options: ['Yes, clearly', 'No, never read', 'Unclear/can\'t remember', 'Was not questioned'],
      required: true
    },
    {
      id: 'search_warrant',
      text: 'Did police have a warrant to search your person, vehicle, or property?',
      type: 'choice',
      options: ['Yes, showed warrant', 'No warrant shown', 'Don\'t know', 'No search conducted'],
      required: true
    },
    {
      id: 'witness_present',
      text: 'Were there witnesses present during the incident?',
      type: 'yes_no',
      required: true
    },
    {
      id: 'prior_record',
      text: 'Do you have any prior criminal convictions?',
      type: 'yes_no',
      required: true
    }
  ],
  employment: [
    {
      id: 'employment_type',
      text: 'What was your employment status?',
      type: 'choice',
      options: ['Full-time employee', 'Part-time employee', 'Contract worker', 'At-will employee'],
      required: true
    },
    {
      id: 'termination_reason',
      text: 'What reason were you given for termination (if any)?',
      type: 'textarea',
      required: false,
      hint: 'Leave blank if no reason was provided'
    },
    {
      id: 'protected_class',
      text: 'Do you believe you were discriminated against based on a protected characteristic?',
      type: 'choice',
      options: ['No', 'Race/ethnicity', 'Gender', 'Age', 'Disability', 'Religion', 'Sexual orientation', 'Other'],
      required: true
    },
    {
      id: 'complaint_filed',
      text: 'Did you file any internal complaints or report issues before termination?',
      type: 'yes_no',
      required: true
    },
    {
      id: 'documentation',
      text: 'Do you have any documentation related to your employment or termination?',
      type: 'textarea',
      required: false,
      hint: 'Emails, performance reviews, policies, etc.'
    },
    {
      id: 'wages_owed',
      text: 'Are you owed any unpaid wages, overtime, or benefits?',
      type: 'yes_no',
      required: true
    }
  ]
};

export function DefenseInterview({ caseType, onComplete, initialMessage }: DefenseInterviewProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const questions = questionsByType[caseType] || [];
  const currentQ = questions[currentQuestion];
  const progress = questions.length > 0 ? ((currentQuestion + 1) / questions.length) * 100 : 0;

  useEffect(() => {
    if (initialMessage && !sessionId) {
      startDefenseSession();
    }
  }, [initialMessage]);

  const startDefenseSession = async () => {
    try {
      const response = await fetch('/api/v1/qa/defense-builder/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: initialMessage || `I need help with a ${caseType} case` })
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
      }
    } catch (error) {
      console.error('Failed to start defense session:', error);
    }
  };

  const validateAnswer = (value: string): string | null => {
    if (!currentQ) return null;

    if (currentQ.required && !value.trim()) {
      return 'This field is required';
    }

    if (currentQ.validation) {
      return currentQ.validation(value);
    }

    return null;
  };

  const handleAnswer = async (answer: string) => {
    const error = validateAnswer(answer);
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    const newAnswers = { ...answers, [currentQ.id]: answer };
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setInputValue('');
    } else {
      await generateDefenseStrategy(newAnswers);
    }
  };

  const generateDefenseStrategy = async (finalAnswers: Record<string, string>) => {
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/defense/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: `Case Type: ${caseType}\n\nCollected Information:\n${
            Object.entries(finalAnswers)
              .map(([key, value]) => `${key}: ${value}`)
              .join('\n')
          }`,
          document_analysis: {
            document_type: caseType,
            summary: `${caseType} case with ${Object.keys(finalAnswers).length} data points collected`,
            parties: ['Client'],
            key_terms: [caseType, ...Object.keys(finalAnswers)],
            collected_answers: finalAnswers
          },
          case_context: {
            interview_completed: true,
            total_questions: questions.length,
            case_type: caseType
          }
        })
      });

      if (response.ok) {
        const defenseStrategy = await response.json();
        onComplete({
          ...defenseStrategy,
          interview_data: finalAnswers,
          case_type: caseType
        });
      } else {
        throw new Error('Failed to generate defense strategy');
      }
    } catch (error) {
      console.error('Error generating defense strategy:', error);
      onComplete({
        error: 'Failed to generate defense strategy',
        interview_data: finalAnswers,
        case_type: caseType
      });
    } finally {
      setIsLoading(false);
    }
  };

  const goBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setInputValue(answers[questions[currentQuestion - 1].id] || '');
      setValidationError(null);
    }
  };

  const renderQuestionInput = (question: Question) => {
    const commonProps = {
      value: inputValue,
      onChange: (e: any) => setInputValue(e.target.value),
      className: validationError ? 'border-red-500' : '',
      onKeyDown: (e: any) => {
        if (e.key === 'Enter' && question.type !== 'textarea') {
          e.preventDefault();
          handleAnswer(inputValue);
        }
      }
    };

    switch (question.type) {
      case 'text':
      case 'email':
        return <Input {...commonProps} type={question.type} placeholder="Enter your answer..." />;

      case 'currency':
        return <Input {...commonProps} type="text" placeholder="$0.00" />;

      case 'date':
        return <Input {...commonProps} type="date" />;

      case 'textarea':
        return <Textarea {...commonProps} placeholder="Provide details..." className="min-h-20" />;

      case 'yes_no':
        return (
          <div className="space-y-2">
            {['Yes', 'No'].map((option) => (
              <Button
                key={option}
                variant={inputValue === option ? 'default' : 'outline'}
                className="w-full justify-start"
                onClick={() => setInputValue(option)}
              >
                {option}
              </Button>
            ))}
          </div>
        );

      case 'choice':
        return (
          <div className="space-y-2">
            {question.options?.map((option) => (
              <Button
                key={option}
                variant={inputValue === option ? 'default' : 'outline'}
                className="w-full justify-start text-left"
                onClick={() => setInputValue(option)}
              >
                {option}
              </Button>
            ))}
          </div>
        );

      default:
        return <Input {...commonProps} placeholder="Enter your answer..." />;
    }
  };

  if (questions.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Case Type Not Supported</h3>
            <p className="text-gray-600">
              We don't have interview questions configured for "{caseType}" cases yet.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-medium mb-2">Analyzing Your Case</h3>
            <p className="text-gray-600">
              Generating personalized defense strategies based on your responses...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-600" />
            Defense Strategy Interview - {caseType.charAt(0).toUpperCase() + caseType.slice(1)} Case
          </CardTitle>
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Question {currentQuestion + 1} of {questions.length}</span>
              <span>{Math.round(progress)}% complete</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium mb-2">{currentQ?.text}</h3>
              {currentQ?.hint && (
                <p className="text-sm text-gray-600 mb-4 p-3 bg-blue-50 rounded-md border-l-4 border-blue-200">
                  💡 {currentQ.hint}
                </p>
              )}
            </div>

            {renderQuestionInput(currentQ)}

            {validationError && (
              <p className="text-red-500 text-sm">{validationError}</p>
            )}
          </div>

          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={goBack}
              disabled={currentQuestion === 0}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>

            <Button
              onClick={() => handleAnswer(inputValue)}
              disabled={!inputValue.trim() && currentQ?.required}
              className="flex items-center gap-2"
            >
              {currentQuestion < questions.length - 1 ? (
                <>
                  Next
                  <ArrowRight className="h-4 w-4" />
                </>
              ) : (
                <>
                  Generate Strategy
                  <CheckCircle className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {Object.keys(answers).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Information Collected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(answers).map(([key, value]) => {
                const question = questions.find(q => q.id === key);
                return (
                  <div key={key} className="flex items-start gap-3 p-3 bg-gray-50 rounded-md">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-700">
                        {question?.text || key}
                      </div>
                      <div className="text-gray-900">{value}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default DefenseInterview;