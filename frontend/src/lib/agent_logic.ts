/**
 * Legal Interview Agent Logic (TypeScript version)
 * Mirrors the Python agent functionality for frontend API routes
 */

interface AgentBrain {
  memory: Record<string, any>;
  insights: string[];
  red_flags: string[];
  opportunities: string[];
  strategy: Record<string, any>;
}

interface Question {
  id: string;
  question: string;
  options?: string[];
  type?: string;
  importance?: string;
  reason?: string;
  follow_ups?: Record<string, string>;
  defense_impact?: Record<string, string>;
}

interface QuestionTree {
  tier_1_critical?: Question[];
  tier_2_important?: Question[];
  tier_3_strategic?: Question[];
}

export class LegalInterviewAgentTS {
  sessionId: string;
  brain: AgentBrain;
  conversationState: string;
  questionCount: number;
  maxQuestions: number;
  documentType: string | null;
  questionTree: QuestionTree;
  askedQuestions: string[];
  followUpNeeded: Array<{ question: string; reason?: string }>;
  defenseStrength: Record<string, number>;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
    this.brain = {
      memory: {},
      insights: [],
      red_flags: [],
      opportunities: [],
      strategy: {}
    };
    this.conversationState = 'initial';
    this.questionCount = 0;
    this.maxQuestions = 10;
    this.documentType = null;
    this.questionTree = {};
    this.askedQuestions = [];
    this.followUpNeeded = [];
    this.defenseStrength = {};
  }

  analyzeDocumentDeeply(documentText: string): any {
    // Simplified analysis for frontend
    const analysis = {
      case_type: 'debt_collection',
      plaintiff_name: this.extractPlaintiffName(documentText),
      amount_claimed: this.extractAmount(documentText),
      summary: 'Document analyzed successfully'
    };

    this.brain.memory['document_analysis'] = analysis;
    this.buildQuestionStrategy(analysis);

    return analysis;
  }

  private extractPlaintiffName(text: string): string {
    const match = text.match(/Plaintiff[,:]?\s+([A-Z][A-Za-z\s,\.]+)/);
    return match ? match[1].trim() : 'Unknown Plaintiff';
  }

  private extractAmount(text: string): string {
    const match = text.match(/\$[\d,]+\.?\d*/);
    return match ? match[0] : '$0';
  }

  private buildQuestionStrategy(analysis: any): void {
    this.questionTree = this.buildDebtQuestionTree(analysis);
  }

  private buildDebtQuestionTree(analysis: any): QuestionTree {
    return {
      tier_1_critical: [
        {
          id: 'last_payment',
          question: 'This is crucial for your defense: When did you make your LAST payment on this account?',
          options: [
            'Within the last year',
            '1-2 years ago',
            '2-4 years ago',
            '4-6 years ago',
            'Over 6 years ago',
            'Never made any payments'
          ],
          follow_ups: {
            'Over 6 years ago': 'Do you have proof of when you last paid (bank statements, cancelled checks)?',
            '4-6 years ago': 'Did you ever acknowledge this debt in writing after that last payment?',
            'Never made any payments': 'Did you ever agree to pay this debt or sign anything?'
          },
          defense_impact: {
            'Over 6 years ago': 'STRONG statute of limitations defense',
            '4-6 years ago': 'Possible statute of limitations depending on state',
            'Never made any payments': 'May dispute validity entirely'
          }
        },
        {
          id: 'debt_recognition',
          question: `The plaintiff ${analysis.plaintiff_name} claims you owe ${analysis.amount_claimed}. Do you recognize this debt?`,
          options: [
            'Yes, I had an account with them',
            'Yes, but not with this company',
            'The amount is wrong',
            'I don\'t recognize this at all',
            'This was already paid/settled',
            'This is identity theft/fraud'
          ],
          follow_ups: {
            'Yes, but not with this company': 'Who was the original creditor?',
            'The amount is wrong': 'What should the correct amount be?',
            'This was already paid/settled': 'Do you have proof of payment or settlement?',
            'This is identity theft/fraud': 'Have you filed a police report or identity theft affidavit?'
          }
        }
      ],
      tier_2_important: [
        {
          id: 'payment_history',
          question: 'Do you have any records of payments you made on this account?',
          options: [
            'Yes, I have bank statements',
            'Yes, I have cancelled checks',
            'Yes, I have receipts',
            'Some records but not all',
            'No records'
          ],
          defense_impact: {
            'Yes, I have bank statements': 'Can prove payments and last payment date',
            'No records': 'Will need to request from plaintiff'
          }
        },
        {
          id: 'hardship',
          question: 'What caused you to stop making payments?',
          options: [
            'Lost job/income',
            'Medical emergency',
            'Divorce/separation',
            'Disability',
            'Dispute with creditor',
            'Could never afford it'
          ]
        }
      ],
      tier_3_strategic: [
        {
          id: 'settlement_attempts',
          question: 'Have you ever tried to settle or negotiate this debt?',
          options: [
            'Yes, they refused my offer',
            'Yes, we had an agreement they broke',
            'Yes, currently negotiating',
            'No, never contacted them',
            'They never contacted me'
          ]
        }
      ]
    };
  }

  getNextIntelligentQuestion(): Question | null {
    // Check for follow-ups first
    if (this.followUpNeeded.length > 0) {
      const followUp = this.followUpNeeded.shift()!;
      return {
        id: 'follow_up_' + Date.now(),
        question: followUp.question,
        type: 'follow_up',
        importance: 'HIGH',
        reason: followUp.reason
      };
    }

    // Go through question tiers
    for (const tier of ['tier_1_critical', 'tier_2_important', 'tier_3_strategic']) {
      const tierQuestions = this.questionTree[tier as keyof QuestionTree] || [];
      for (const q of tierQuestions) {
        if (!this.askedQuestions.includes(q.id)) {
          this.askedQuestions.push(q.id);
          this.questionCount++;
          return {
            ...q,
            question_number: this.questionCount,
            total_questions: this.maxQuestions
          };
        }
      }
    }

    return null;
  }

  processAnswerIntelligently(questionId: string, answer: string): any {
    // Store answer
    this.brain.memory[questionId] = answer;

    // Find question data
    const questionData = this.findQuestionData(questionId);

    // Generate intelligent feedback
    const feedback = this.generateFeedback(questionId, answer, questionData);

    // Check for follow-ups
    if (questionData?.follow_ups && questionData.follow_ups[answer]) {
      this.followUpNeeded.push({
        question: questionData.follow_ups[answer],
        reason: `Following up on: ${answer}`
      });
    }

    // Check defense impact
    const insights: string[] = [];
    if (questionData?.defense_impact && questionData.defense_impact[answer]) {
      const impact = questionData.defense_impact[answer];
      this.brain.insights.push(impact);
      insights.push(impact);
      this.updateDefenseStrength(impact);
    }

    return {
      insights,
      feedback,  // Add intelligent feedback
      defense_implications: this.brain.insights[this.brain.insights.length - 1] || null,
      follow_up_needed: this.followUpNeeded.length > 0
    };
  }

  private generateFeedback(questionId: string, answer: string, questionData: Question | null): string {
    // Provide intelligent, contextual feedback based on the answer

    // Statute of Limitations feedback
    if (questionId === 'last_payment') {
      if (answer === 'Over 6 years ago') {
        return '✅ Excellent! This is a very strong defense. Debts over 6 years old are typically beyond the statute of limitations in most states. This could be a complete defense that gets the case dismissed.';
      } else if (answer === '4-6 years ago') {
        return '⚖️ This is promising. Many states have a 4-6 year statute of limitations. We\'ll need to verify your state\'s specific timeframe, but this could be a viable defense.';
      } else if (answer === '2-4 years ago') {
        return '📋 This timeframe is important. While it may be within the statute in some states, it\'s worth investigating further. Some states have shorter periods for certain types of debt.';
      } else if (answer === 'Within the last year' || answer === '1-2 years ago') {
        return '📝 The debt appears to be within the statute of limitations. We\'ll focus on other defenses like standing, amount disputes, or procedural issues.';
      } else if (answer === 'Never made any payments') {
        return '🔍 Important detail! If you never made payments, we need to determine if you even had an agreement with them. This could challenge the validity of the entire debt.';
      }
    }

    // Debt recognition feedback
    if (questionId === 'debt_recognition') {
      if (answer === 'Yes, but not with this company') {
        return '🎯 Critical insight! This suggests the debt may have been sold to a debt buyer. They must prove they legally own the debt with proper documentation. Many debt buyers lack this proof.';
      } else if (answer === 'The amount is wrong') {
        return '💡 Amount disputes are common and winnable. They must prove every dollar claimed. Even small errors can undermine their entire case.';
      } else if (answer === 'I don\'t recognize this at all') {
        return '⚠️ This is significant! You may be able to dispute the debt\'s validity entirely. They must prove you owe this debt, and you\'re not required to prove you don\'t.';
      } else if (answer === 'This was already paid/settled') {
        return '✅ If you have proof of payment or settlement, this could result in immediate dismissal. Documentation is key here.';
      } else if (answer === 'This is identity theft/fraud') {
        return '🚨 This is a serious matter with strong legal protections. Identity theft is a complete defense, but requires documentation (police report, FTC affidavit).';
      } else if (answer === 'Yes, I had an account with them') {
        return '📝 Acknowledged. Even if you recognize the account, they still must prove the amount, ownership, and that it\'s within the statute of limitations.';
      }
    }

    // Payment history feedback
    if (questionId === 'payment_history') {
      if (answer.includes('Yes, I have')) {
        return '🎯 Excellent! Documentation is crucial. These records can prove your last payment date for statute of limitations and show payment history to dispute amounts.';
      } else if (answer === 'Some records but not all') {
        return '📋 Partial records are still valuable. We can also request complete records from the plaintiff through discovery - they\'re required to provide them.';
      } else if (answer === 'No records') {
        return '⚖️ No problem. You can request all records from the plaintiff. They must provide documentation of payments, which may work in your favor if their records are incomplete.';
      }
    }

    // Hardship feedback
    if (questionId === 'hardship') {
      if (answer === 'Lost job/income' || answer === 'Medical emergency' || answer === 'Disability') {
        return '💙 This context is important for potential settlement negotiations and may provide grounds for hardship-based relief or payment plans.';
      } else if (answer === 'Dispute with creditor') {
        return '🔍 Disputes with the original creditor can be relevant defenses. Document everything about the dispute - it may show they breached the contract first.';
      }
    }

    // Settlement attempts feedback
    if (questionId === 'settlement_attempts') {
      if (answer === 'Yes, they refused my offer') {
        return '📝 Their refusal to negotiate shows they may be unwilling to settle. This strengthens our position to fight the case aggressively.';
      } else if (answer === 'Yes, we had an agreement they broke') {
        return '⚠️ A broken settlement agreement could be a breach of contract on their part. This is a potential defense or counterclaim.';
      } else if (answer === 'They never contacted me') {
        return '🔍 Lack of communication before suing may indicate procedural issues or suggest they\'re not the true owner of the debt.';
      }
    }

    // Default feedback
    return '✓ Noted. This information will help build your comprehensive defense strategy.';
  }

  private findQuestionData(questionId: string): Question | null {
    for (const tier of ['tier_1_critical', 'tier_2_important', 'tier_3_strategic']) {
      const tierQuestions = this.questionTree[tier as keyof QuestionTree] || [];
      const found = tierQuestions.find(q => q.id === questionId);
      if (found) return found;
    }
    return null;
  }

  private updateDefenseStrength(impact: string): void {
    if (impact.includes('STRONG')) {
      if (impact.toLowerCase().includes('statute of limitations')) {
        this.defenseStrength['statute_of_limitations'] = 90;
      } else if (impact.toLowerCase().includes('standing')) {
        this.defenseStrength['lack_of_standing'] = 85;
      }
    } else if (impact.includes('Possible')) {
      if (impact.toLowerCase().includes('statute of limitations')) {
        this.defenseStrength['statute_of_limitations'] = 60;
      }
    }
  }

  buildComprehensiveDefenseStrategy(): any {
    const defenses = [];

    // Statute of Limitations
    if (this.brain.memory['last_payment']) {
      const solDefense = this.analyzeStatuteOfLimitations();
      if (solDefense.applicable) {
        defenses.push(solDefense);
      }
    }

    // Standing
    const standingDefense = this.analyzeStanding();
    if (standingDefense.issues_found) {
      defenses.push(standingDefense);
    }

    // Sort by strength
    defenses.sort((a, b) => (b.strength || 0) - (a.strength || 0));

    return {
      primary_defenses: defenses.slice(0, 3),
      secondary_defenses: defenses.slice(3, 6),
      immediate_actions: this.generateActionPlan(),
      evidence_needed: this.identifyEvidenceNeeds(),
      negotiation_leverage: 'Moderate leverage based on identified defenses',
      estimated_success_rate: this.calculateOverallSuccessRate()
    };
  }

  private analyzeStatuteOfLimitations(): any {
    const lastPayment = this.brain.memory['last_payment'] || '';
    const yearsMap: Record<string, number> = {
      'Within the last year': 0.5,
      '1-2 years ago': 1.5,
      '2-4 years ago': 3,
      '4-6 years ago': 5,
      'Over 6 years ago': 7
    };

    const years = yearsMap[lastPayment];

    if (years && years >= 4) {
      const strength = years >= 6 ? 95 : 75;
      const strengthLevel = strength >= 90 ? 'VERY STRONG' : strength >= 70 ? 'STRONG' : 'MODERATE';

      return {
        name: 'Statute of Limitations Defense',
        applicable: true,
        strength: strength,
        strength_level: strengthLevel,
        description: `The debt appears to be approximately ${years} years old, which likely exceeds the statute of limitations for debt collection in most states.`,
        detailed_explanation: `
## Why This Defense Works

Based on your last payment being **${lastPayment}**, this debt has aged beyond the legal collection period in most jurisdictions.

### Legal Background
- Most states impose a 3-6 year statute of limitations on debt collection actions
- The clock typically starts from the date of last payment or last account activity
- Once expired, the debt becomes "time-barred" and legally unenforceable
- Creditors cannot win a lawsuit on time-barred debt if properly asserted

### Your Specific Situation
- **Last Payment:** ${lastPayment} (approximately ${years} years ago)
- **Likely Statute Period:** 4-6 years (varies by state)
- **Current Status:** Debt appears time-barred
- **Success Likelihood:** ${strength}% - This is a ${strengthLevel} defense

### Critical Points
1. **Burden on Plaintiff:** They must prove the debt is within the statute, not you
2. **Affirmative Defense:** You must explicitly raise this in your Answer
3. **Don't Acknowledge:** Avoid any written acknowledgment of owing the debt (can restart the clock)
4. **State-Specific:** Research your state's exact statute period for this type of debt

### What Happens If Successful
- Case dismissed entirely
- No judgment against you
- No wage garnishment or bank levies
- Clean resolution without payment
        `,
        requirements: [
          'Proof of last payment date (bank statements, cancelled checks, payment records)',
          'Documentation showing no written acknowledgment after last payment',
          'Research of your specific state\'s statute of limitations period',
          'Proof of no partial payments that could have restarted the clock'
        ],
        how_to_assert: `
**In Your Answer (Affirmative Defense Section):**

"AFFIRMATIVE DEFENSE - STATUTE OF LIMITATIONS

Plaintiff's claim is barred by the applicable statute of limitations. The alleged debt, if it exists, arose more than [X] years ago, exceeding the statutory period for bringing such claims under [State] law. Plaintiff has failed to file this action within the time permitted by law."

**In Discovery Requests:**

1. Request: "Date of last payment received on this account"
2. Request: "All documents showing account activity after [date]"
3. Request: "Any written acknowledgments of debt from defendant"
        `,
        winning_scenarios: [
          'Plaintiff cannot prove debt is within statute',
          'Their records show last activity beyond statutory period',
          'No evidence of debt acknowledgment or partial payments',
          'Court grants motion to dismiss based on this defense'
        ],
        risks_to_avoid: [
          'Making any payment (restarts the clock)',
          'Writing anything acknowledging you owe the debt',
          'Agreeing to payment plans',
          'Missing the deadline to file your Answer'
        ]
      };
    }

    return { applicable: false };
  }

  private analyzeStanding(): any {
    const issues: string[] = [];
    const details: string[] = [];
    let strength = 0;

    const docAnalysis = this.brain.memory['document_analysis'] || {};
    const debtRecognition = this.brain.memory['debt_recognition'] || '';

    // Check if debt buyer
    const isDebtBuyer = docAnalysis.plaintiff_name?.toLowerCase().includes('midland') ||
                        docAnalysis.plaintiff_name?.toLowerCase().includes('portfolio') ||
                        docAnalysis.plaintiff_name?.toLowerCase().includes('lvnv') ||
                        docAnalysis.plaintiff_name?.toLowerCase().includes('cavalry');

    if (isDebtBuyer) {
      issues.push('Plaintiff is a debt buyer, not the original creditor');
      details.push('Debt buyers often lack proper documentation');
      strength += 40;
    }

    // Check if user doesn't recognize plaintiff
    if (debtRecognition === 'Yes, but not with this company') {
      issues.push('Defendant does not recognize plaintiff as creditor');
      details.push('No direct relationship with plaintiff established');
      strength += 35;
    }

    // Check for missing contract
    if (!docAnalysis.contract_attached) {
      issues.push('No original contract attached to complaint');
      details.push('Cannot verify terms or agreement');
      strength += 25;
    }

    if (issues.length > 0) {
      const finalStrength = Math.min(strength, 90);
      const strengthLevel = finalStrength >= 80 ? 'VERY STRONG' : finalStrength >= 60 ? 'STRONG' : 'MODERATE';

      return {
        name: 'Lack of Standing / Improper Ownership',
        issues_found: true,
        strength: finalStrength,
        strength_level: strengthLevel,
        description: 'Plaintiff has failed to prove they legally own this debt and have the right to collect it.',
        detailed_explanation: `
## Why This Defense Works

The plaintiff must prove they have **legal standing** to sue you - meaning they must show they actually own the debt and have the right to collect it.

### Issues Identified
${issues.map((issue, i) => `${i + 1}. ${issue}`).join('\n')}

### Legal Requirements for Standing
To have standing, the plaintiff MUST prove:
1. **Ownership:** They currently own the debt
2. **Chain of Title:** Complete paper trail showing how debt was transferred
3. **Original Agreement:** Terms of the original contract
4. **Assignment:** Valid transfer from original creditor (if debt was sold)

### Common Standing Problems with Debt Buyers

**Documentation Failures:**
- Missing original signed contract
- Incomplete assignment documents
- No proof of consideration (payment) for debt purchase
- Chain of title has gaps or breaks
- Affidavits from people with no personal knowledge

**Legal Standards:**
- Debt buyers must prove EVERY link in the chain of ownership
- They cannot rely on computer printouts or business records alone
- They must have actual documents showing transfer of debt
- Hearsay evidence is generally not admissible

### Your Specific Case
- **Plaintiff:** ${docAnalysis.plaintiff_name || 'Unknown'}
- **Standing Issues:** ${issues.length} identified
- **Strength Rating:** ${finalStrength}% - ${strengthLevel}
${details.map(d => `- ${d}`).join('\n')}

### What This Means
If the plaintiff cannot prove standing, the case MUST be dismissed regardless of whether you actually owe the debt. Standing is a threshold requirement - without it, they cannot proceed.

### Strategic Advantage
Many debt buyers purchase debts in bulk for pennies on the dollar WITHOUT receiving complete documentation. They gamble that defendants won't challenge standing. When challenged, they often cannot meet the burden of proof.
        `,
        requirements: [
          'File Answer denying plaintiff has standing to sue',
          'Request ALL documents in discovery showing chain of ownership',
          'Demand original signed contract with your signature',
          'Request proof of valid assignment from original creditor',
          'Challenge any affidavits as lacking personal knowledge',
          'File motion to dismiss if they cannot prove standing'
        ],
        how_to_assert: `
**In Your Answer:**

"DENIAL OF STANDING

Defendant denies that Plaintiff has standing to bring this action. Defendant specifically denies that Plaintiff is the owner and holder of the alleged debt. Defendant demands strict proof that Plaintiff has legal authority to collect on any alleged debt."

"AFFIRMATIVE DEFENSE - LACK OF STANDING

Plaintiff lacks standing to bring this action as Plaintiff has failed to establish it is the real party in interest and the owner and holder of any alleged debt. Plaintiff has not demonstrated a valid chain of title or assignment of the alleged debt."

**Discovery Requests to Send:**

1. "The original signed contract or agreement creating the alleged debt."

2. "Complete chain of title showing all transfers of the alleged debt from origination to present."

3. "All assignment agreements showing transfer of the alleged debt to Plaintiff."

4. "Proof of consideration paid for any assignment of the alleged debt."

5. "Documents showing Plaintiff's authority to collect on the alleged debt."

6. "Identity and personal knowledge of any affiant who claims knowledge of this account."

**Motion to Dismiss (if they fail to prove standing):**

"Plaintiff has failed to establish standing to bring this action. Without valid assignment documents and chain of title, Plaintiff cannot proceed as it is not the real party in interest."
        `,
        winning_scenarios: [
          'Plaintiff cannot produce original signed contract',
          'Assignment documents are missing or incomplete',
          'Chain of title has gaps or unexplained transfers',
          'Affidavits come from people without personal knowledge',
          'Plaintiff withdraws case rather than prove standing',
          'Court grants motion to dismiss for lack of standing'
        ],
        risks_to_avoid: [
          'Admitting you owe the debt (separate from who can collect)',
          'Accepting they own it without demanding proof',
          'Failing to challenge standing in Answer',
          'Not requesting ownership documents in discovery'
        ],
        case_law_support: [
          'Debt buyers must prove chain of ownership with actual documents',
          'Computer printouts alone insufficient to prove standing',
          'Plaintiff bears burden of proving standing at all stages',
          'Affidavits without personal knowledge are inadmissible hearsay'
        ]
      };
    }

    return { issues_found: false };
  }

  private generateActionPlan(): any[] {
    return [
      {
        action: 'File Answer',
        deadline: '20-30 days from service',
        priority: 'CRITICAL',
        details: 'Must file answer with court and serve on plaintiff attorney',
        how_to: '1. Use court\'s answer form or create your own\n2. Respond to each numbered allegation\n3. Include all affirmative defenses\n4. File with court clerk\n5. Mail copy to plaintiff\'s attorney (certified mail)'
      },
      {
        action: 'Request Discovery',
        deadline: 'With or shortly after answer',
        priority: 'HIGH',
        details: 'Demand all documents supporting their claim'
      },
      {
        action: 'Gather Your Evidence',
        deadline: 'Immediately',
        priority: 'HIGH',
        details: 'Collect all documents supporting your defense'
      }
    ];
  }

  private identifyEvidenceNeeds(): string[] {
    return [
      'Proof of last payment date',
      'Bank statements',
      'Any written correspondence',
      'Original contract or account agreement'
    ];
  }

  private calculateOverallSuccessRate(): string {
    const total = Object.values(this.defenseStrength).reduce((sum, val) => sum + val, 0);
    const count = Object.keys(this.defenseStrength).length;

    if (count === 0) return 'Moderate - 40-50%';

    const average = total / count;

    if (average >= 80) return 'Very Strong - 70-80% chance of success';
    if (average >= 60) return 'Strong - 60-70% chance of success';
    if (average >= 40) return 'Moderate - 40-60% chance of success';
    return 'Challenging - 30-40% chance of success';
  }
}

// Global storage for agent instances
export const agentInstances: Record<string, LegalInterviewAgentTS> = {};
