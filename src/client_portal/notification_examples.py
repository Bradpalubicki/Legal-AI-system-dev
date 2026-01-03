"""
Notification Examples and Demonstrations

Provides comprehensive examples of how the intelligent notification system
translates complex legal events into plain English for different client types.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

from .intelligent_notification_system import (
    IntelligentNotificationSystem, ComplexityLevel, TranslationContext, IntelligentNotification
)
from .notification_enhancement import (
    NotificationEnhancementEngine, SentimentType, ClientPersonality, DeliveryChannel
)


@dataclass
class NotificationExample:
    """Example notification showing before/after translation."""
    scenario: str
    client_type: str
    original_legal_text: str
    translated_versions: Dict[ComplexityLevel, str]
    sentiment: SentimentType
    urgency_score: int
    recommended_actions: List[str]
    explanation: str


class NotificationExamples:
    """Collection of example notifications for different scenarios."""
    
    def __init__(self):
        self.examples = self._create_examples()
    
    def get_all_examples(self) -> List[NotificationExample]:
        """Get all notification examples."""
        return self.examples
    
    def get_examples_by_context(self, context: TranslationContext) -> List[NotificationExample]:
        """Get examples for a specific context."""
        return [ex for ex in self.examples if context.value in ex.scenario.lower()]
    
    def get_examples_by_client_type(self, client_type: str) -> List[NotificationExample]:
        """Get examples for a specific client type."""
        return [ex for ex in self.examples if ex.client_type == client_type]
    
    def _create_examples(self) -> List[NotificationExample]:
        """Create comprehensive examples of notification translations."""
        return [
            # Settlement Offer Examples
            NotificationExample(
                scenario="Settlement Offer - Personal Injury Case",
                client_type="individual_anxious",
                original_legal_text="Opposing counsel has tendered a settlement offer of $75,000 in full satisfaction of all claims, demands, and causes of action arising from the motor vehicle collision of March 15, 2024. The offer is contingent upon execution of a comprehensive general release and dismissal with prejudice of all pending litigation. Plaintiff has 15 days to accept or reject this proposal.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "Hi Sarah, the other driver's lawyer has offered to pay you $75,000 to settle your car accident case. This means you would get this money and your case would be finished. You have 15 days to decide if you want to accept this offer or not. We think this is a fair amount for your injuries. Let us know what you want to do!",
                    
                    ComplexityLevel.MODERATE: "We've received a settlement offer of $75,000 for your car accident case. The other side is willing to pay this amount to resolve your case without going to trial. If you accept, you'll receive the money and the case will be closed. You have 15 days to make your decision. Based on your injuries and medical bills, we believe this is a reasonable offer. We can discuss the pros and cons when you're ready.",
                    
                    ComplexityLevel.DETAILED: "The defendant's insurance company has made a settlement offer of $75,000 to resolve your personal injury case from the March 15, 2024 motor vehicle accident. This offer would settle all claims related to the accident in exchange for a full legal release. You have 15 days to respond. Accepting means you'll receive $75,000 but cannot pursue additional compensation later. We've reviewed this against similar cases and your medical expenses, and believe it's within a reasonable range. We recommend discussing this thoroughly before deciding."
                },
                sentiment=SentimentType.POSITIVE,
                urgency_score=7,
                recommended_actions=[
                    "Review your medical bills and lost wages",
                    "Consider your ongoing treatment needs",
                    "Discuss with family if desired",
                    "Schedule a call with us to review the offer"
                ],
                explanation="Settlement offers are opportunities to resolve your case without the uncertainty and expense of going to trial."
            ),
            
            # Court Filing Example
            NotificationExample(
                scenario="Motion for Summary Judgment Filed",
                client_type="business_formal",
                original_legal_text="Defendants have filed a Motion for Summary Judgment pursuant to Federal Rule of Civil Procedure 56, asserting that no genuine issues of material fact exist and that they are entitled to judgment as a matter of law. The motion challenges the sufficiency of plaintiff's evidence regarding the breach of contract claim and seeks dismissal of Count I of the complaint. A response brief is due within 21 days of service.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "The other company has asked the judge to end your case without a trial. They say you don't have enough proof that they broke your contract. We need to write a response by [date] showing why your case should continue. Don't worry - this is normal, and we have strong evidence to fight this request.",
                    
                    ComplexityLevel.MODERATE: "The defendant has filed a motion asking the judge to dismiss your breach of contract case without going to trial. They claim you don't have sufficient evidence to prove they violated your agreement. We have 21 days to file our response, which will present all the evidence supporting your case. This is a standard legal tactic, and we're prepared to oppose it with the documentation we've gathered.",
                    
                    ComplexityLevel.DETAILED: "Defendants have filed a Motion for Summary Judgment challenging the sufficiency of evidence for your breach of contract claim. They argue no genuine factual disputes exist and they should win as a matter of law. We have 21 days to file our opposition brief, which will include all evidence of the contract breach, damages calculations, and witness statements. Summary judgment motions are common in commercial litigation and we have strong documentation to defeat this motion."
                },
                sentiment=SentimentType.NEUTRAL,
                urgency_score=5,
                recommended_actions=[
                    "We'll review all evidence and documentation",
                    "Prepare comprehensive response brief",
                    "Gather any additional supporting materials",
                    "Keep you informed of our filing and next steps"
                ],
                explanation="A motion for summary judgment is the other side's attempt to win without a trial by claiming insufficient evidence exists."
            ),
            
            # Discovery Deadline Example
            NotificationExample(
                scenario="Discovery Deadline Approaching",
                client_type="individual_moderate",
                original_legal_text="Pursuant to the Court's Scheduling Order dated October 1, 2024, all fact discovery must be completed by December 15, 2024. This includes the production of all responsive documents, completion of depositions, and service of interrogatory responses. Expert witness disclosures are due by January 15, 2025. Failure to comply with these deadlines may result in sanctions including the exclusion of evidence or dismissal of claims.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "We have an important deadline coming up on December 15th. By this date, we need to finish gathering all the information and evidence for your case. This includes collecting documents and taking sworn statements from witnesses. We're on track to meet this deadline and will handle everything for you.",
                    
                    ComplexityLevel.MODERATE: "We have a court-ordered deadline of December 15, 2024 to complete all evidence gathering (called 'discovery') in your case. This includes collecting documents, conducting depositions (sworn testimony), and exchanging information with the other side. We also need to identify our expert witnesses by January 15, 2025. We're actively working to meet all these deadlines.",
                    
                    ComplexityLevel.DETAILED: "The court has set December 15, 2024 as the deadline to complete all fact discovery in your case. This encompasses document production, depositions of key witnesses, and responses to written questions (interrogatories). Expert witness disclosures are due January 15, 2025. These deadlines are strictly enforced, and non-compliance can result in sanctions. We have a comprehensive plan in place to complete all discovery requirements timely."
                },
                sentiment=SentimentType.NEUTRAL,
                urgency_score=6,
                recommended_actions=[
                    "Continue gathering requested documents",
                    "Prepare for your deposition if scheduled",
                    "Review any questions we send you promptly",
                    "Let us know if you remember any additional relevant information"
                ],
                explanation="Discovery is the process where both sides gather evidence and information to prepare for trial."
            ),
            
            # Billing/Invoice Example
            NotificationExample(
                scenario="Monthly Invoice Generated",
                client_type="business_formal",
                original_legal_text="Please find attached Invoice No. 2024-1157 in the amount of $12,450.00 for professional services rendered during the period of October 1-31, 2024. The invoice includes 47.5 hours of attorney time at $350/hour ($16,625.00), 23.2 hours of paralegal time at $150/hour ($3,480.00), plus costs for court filing fees ($402.00), deposition transcripts ($1,250.00), and expert witness fees ($2,500.00). Payment is due within 30 days of invoice date pursuant to the retainer agreement.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "Your bill for October is $12,450. This covers the work we did on your case last month, including court filings and expert witness fees. You can pay online through your portal or by check. Payment is due by [date]. Thank you for your business!",
                    
                    ComplexityLevel.MODERATE: "We've prepared your October invoice for $12,450, which covers 47.5 hours of attorney work, 23.2 hours of paralegal support, and various case expenses including court fees and expert witnesses. This reflects significant progress on your case during discovery. Payment is due within 30 days, and you can pay securely through your client portal.",
                    
                    ComplexityLevel.DETAILED: "Your October 2024 invoice totals $12,450 for comprehensive legal services including: 47.5 attorney hours ($16,625), 23.2 paralegal hours ($3,480), court filing fees ($402), deposition transcripts ($1,250), and expert witness fees ($2,500). This month involved intensive discovery work and expert consultations. Payment terms are net 30 days per your retainer agreement."
                },
                sentiment=SentimentType.NEUTRAL,
                urgency_score=3,
                recommended_actions=[
                    "Review the detailed invoice in your portal",
                    "Contact us with any questions about charges",
                    "Make payment by the due date",
                    "Set up autopay if desired for future invoices"
                ],
                explanation="Monthly invoices detail all work performed and expenses incurred on your case."
            ),
            
            # Negative Case Development
            NotificationExample(
                scenario="Motion Denied - Setback",
                client_type="individual_anxious",
                original_legal_text="The Court has denied Plaintiff's Motion for Partial Summary Judgment on the issue of liability. In a 12-page Order dated November 3, 2024, the Court held that genuine issues of material fact exist regarding the defendant's duty of care and causation, precluding summary judgment. The Court noted that while plaintiff's evidence is substantial, defendant's expert report raises sufficient questions about industry standards to require a jury determination. The case will proceed to trial as scheduled for February 2025.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "Hi Maria, I have an update on your case. The judge decided not to rule in our favor on our early request to win part of your case. This doesn't mean we're losing - it just means we need to prove our case at trial instead of winning early. The other side's expert raised some questions that the judge wants a jury to decide. We still have a strong case and are preparing for your February trial.",
                    
                    ComplexityLevel.MODERATE: "The judge has denied our motion asking for a partial win in your case. While this is disappointing, it doesn't weaken our overall position. The court found that the other side's expert witness created enough questions about the facts that a jury should decide rather than the judge. This is actually common in complex cases like yours. We're now focusing all our energy on preparing for the February 2025 trial, where we'll present your full case to a jury.",
                    
                    ComplexityLevel.DETAILED: "The Court has denied our Motion for Partial Summary Judgment on liability. In a detailed 12-page order, the judge acknowledged our substantial evidence but found that defendant's expert report creates genuine factual disputes requiring jury resolution. Specifically, the court noted questions about duty of care standards and causation that prevent a legal determination at this stage. This decision is not uncommon in complex liability cases, and we remain confident in our trial strategy for February 2025."
                },
                sentiment=SentimentType.NEGATIVE,
                urgency_score=4,
                recommended_actions=[
                    "We'll adjust our trial preparation strategy",
                    "Strengthen our expert witness testimony",
                    "Continue gathering supportive evidence",
                    "Prepare you thoroughly for trial proceedings"
                ],
                explanation="Court rulings don't always go our way, but this doesn't mean your case is weak - it just means we'll prove it at trial instead."
            ),
            
            # Urgent Document Signature
            NotificationExample(
                scenario="Urgent Document Signature Required",
                client_type="individual_moderate",
                original_legal_text="Attached please find the Stipulation for Extension of Discovery Deadline, which must be executed and returned by 5:00 PM today to comply with Local Rule 26.3. Opposing counsel has agreed to extend the discovery cutoff from December 15, 2024 to January 15, 2025, contingent upon court approval and timely filing of this stipulation. Failure to execute this document today will result in the original December 15 deadline remaining in effect, which may prejudice our ability to complete necessary depositions.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "URGENT: We need you to sign an important document today by 5 PM. This document asks the judge to give us more time (until January 15) to gather evidence for your case. If you don't sign it today, we'll have less time to prepare, which could hurt your case. Please sign and return it immediately - you can do this through your portal or email.",
                    
                    ComplexityLevel.MODERATE: "We need your immediate signature on a court document that extends our deadline for gathering evidence from December 15 to January 15. Both sides have agreed to this extension, but we must file it with the court by 5 PM today. This extra month will allow us to complete important witness interviews that strengthen your case. Please sign electronically through your portal or return via email ASAP.",
                    
                    ComplexityLevel.DETAILED: "Please immediately execute the attached Stipulation for Extension of Discovery Deadline. This document, agreed to by both parties, requests court approval to extend our evidence-gathering deadline from December 15, 2024 to January 15, 2025. The extension is crucial for completing depositions of key witnesses that will strengthen your case. Court rules require filing by 5 PM today. Electronic signature is available through your client portal for immediate processing."
                },
                sentiment=SentimentType.URGENT,
                urgency_score=9,
                recommended_actions=[
                    "Sign the document immediately (available in your portal)",
                    "Call us if you have any technical difficulties",
                    "Return via email if portal access isn't working",
                    "Confirm receipt after signing"
                ],
                explanation="Sometimes court deadlines require immediate action to protect your case - this is one of those times."
            ),
            
            # Positive Case Resolution
            NotificationExample(
                scenario="Favorable Settlement Reached",
                client_type="business_formal",
                original_legal_text="We are pleased to report that a comprehensive settlement agreement has been reached in the matter of TechCorp v. DataSystems, Inc., resolving all claims and counterclaims. The settlement provides for payment of $285,000 to TechCorp, dismissal of all litigation with prejudice, execution of mutual general releases, and a confidential business relationship going forward. The settlement documents will be executed within 5 business days, with payment due within 30 days of execution. This resolution avoids the uncertainties and costs of protracted litigation while achieving a favorable financial outcome.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "Excellent news! We've reached a settlement in your case. DataSystems will pay TechCorp $285,000 and the lawsuit will be over. You'll also be able to do business with them again in the future. The papers will be signed within 5 days and you'll receive payment within 30 days. This is a great outcome that saves you time and money compared to going to trial.",
                    
                    ComplexityLevel.MODERATE: "Great news! We've successfully settled your case against DataSystems for $285,000. This settlement resolves all legal claims and allows both companies to potentially work together again in the future. The settlement documents will be finalized within 5 business days, with payment due within 30 days. This outcome avoids the risks and costs of continuing to trial while securing a substantial financial recovery.",
                    
                    ComplexityLevel.DETAILED: "We're pleased to announce a comprehensive settlement agreement in TechCorp v. DataSystems, Inc. Key terms include: (1) $285,000 payment to TechCorp, (2) dismissal of all claims with prejudice, (3) mutual general releases, and (4) framework for future business relationship under confidentiality provisions. Documentation will be executed within 5 business days with payment due within 30 days thereafter. This resolution achieves your primary objectives while eliminating litigation risks and ongoing legal costs."
                },
                sentiment=SentimentType.POSITIVE,
                urgency_score=2,
                recommended_actions=[
                    "Review the settlement terms we've negotiated",
                    "Prepare for document execution next week", 
                    "Plan for payment receipt within 30 days",
                    "Consider future business relationship opportunities"
                ],
                explanation="Settlements allow you to achieve your goals while avoiding the uncertainty and expense of continued litigation."
            ),
            
            # Deposition Scheduling
            NotificationExample(
                scenario="Deposition Scheduled",
                client_type="individual_anxious",
                original_legal_text="Your deposition has been noticed for December 10, 2024, at 9:00 AM at the offices of opposing counsel, located at 123 Legal Plaza, Suite 4500. The deposition will be conducted under oath and recorded by a certified court reporter. You should plan for approximately 4-6 hours, including breaks. Opposing counsel will question you about the facts surrounding the incident, your injuries, medical treatment, and impact on your daily life. We will meet for preparation the day before at 2:00 PM in our office.",
                translated_versions={
                    ComplexityLevel.SIMPLE: "Your deposition (sworn testimony) is scheduled for December 10th at 9 AM. This is when the other lawyer will ask you questions about your accident and injuries. It will last about 4-6 hours with breaks. Don't worry - this is normal and we'll prepare you thoroughly the day before. We'll be right there with you to protect your interests and help you through the process.",
                    
                    ComplexityLevel.MODERATE: "We've scheduled your deposition for December 10, 2024 at 9 AM. A deposition is sworn testimony where the opposing attorney will ask questions about your case, injuries, and how the accident has affected your life. It typically takes 4-6 hours including breaks. We'll meet the day before at 2 PM to prepare you thoroughly. Remember, we'll be there to guide you and object to any improper questions.",
                    
                    ComplexityLevel.DETAILED: "Your deposition is scheduled for December 10, 2024, 9:00 AM at opposing counsel's office (123 Legal Plaza, Suite 4500). During this sworn testimony session, you'll be questioned about the incident facts, medical treatment, ongoing symptoms, and life impact. The session will be recorded by a court reporter and may last 4-6 hours. We'll conduct a comprehensive preparation session on December 9th at 2:00 PM to review likely questions, testimony strategies, and your rights during the deposition."
                },
                sentiment=SentimentType.REASSURING,
                urgency_score=5,
                recommended_actions=[
                    "Mark December 10th on your calendar (full day)",
                    "Attend preparation meeting December 9th at 2 PM",
                    "Review your medical records beforehand",
                    "Get a good night's sleep before your deposition"
                ],
                explanation="A deposition is your opportunity to tell your side of the story under oath, and we'll prepare you thoroughly so you feel confident."
            )
        ]


class PersonalizedExamples:
    """Examples showing how notifications are personalized for different client types."""
    
    @staticmethod
    def get_personality_examples() -> Dict[str, Dict[str, str]]:
        """Get examples of how the same notification varies by personality."""
        
        base_scenario = "Settlement offer of $50,000 received, 10 days to respond"
        
        return {
            "anxious_client": {
                "communication_style": "reassuring and detailed",
                "notification": "Hi Jennifer, we have good news! The other side has offered $50,000 to settle your case. We know legal matters can be stressful, so let us walk you through what this means. This offer is actually quite reasonable based on similar cases we've handled. You have 10 days to decide, but don't worry - we'll discuss all the pros and cons together before you make any decision. We think this could be a good resolution that lets you move forward without the stress of a trial. We're here to support you every step of the way.",
                "next_steps": [
                    "Schedule a phone call to discuss the offer in detail",
                    "We'll explain exactly what accepting means",
                    "Review your options together without any pressure",
                    "Take time to think it over with your family"
                ]
            },
            
            "business_client": {
                "communication_style": "formal and efficient",
                "notification": "We have received a settlement offer of $50,000 for your case. Based on our analysis of comparable cases and litigation risks, this offer falls within the expected range for resolution. You have 10 days to respond. Key considerations include: avoiding ongoing litigation costs estimated at $15,000-25,000, eliminating trial uncertainty, and allowing business focus on operations rather than legal proceedings. We recommend scheduling a brief conference call to review terms and finalize strategy.",
                "next_steps": [
                    "Review detailed settlement analysis in your portal",
                    "Schedule strategic discussion meeting",
                    "Evaluate business impact of continued litigation",
                    "Make informed decision based on cost-benefit analysis"
                ]
            },
            
            "elderly_client": {
                "communication_style": "patient and clear",
                "notification": "Dear Mr. Williams, I wanted to personally update you on your case. The other party has offered to pay $50,000 to settle everything. This means you would receive this money and your case would be finished - no more court dates or legal proceedings. You have 10 days to let us know what you'd like to do. This seems like a fair amount based on your situation. I'd like to sit down with you in person to explain everything clearly and answer any questions you might have. Please don't hesitate to call if you'd like to discuss this right away.",
                "next_steps": [
                    "Schedule in-person meeting at your convenience",
                    "Bring any questions you'd like to discuss",
                    "We can involve family members in the discussion if you'd like",
                    "Take all the time you need to make your decision"
                ]
            },
            
            "tech_savvy_client": {
                "communication_style": "modern and efficient",
                "notification": "🎉 Settlement Update: $50,000 offer received! The opposing party has proposed settling your case for $50,000. You've got 10 days to decide. Check out the detailed breakdown and risk analysis we've uploaded to your portal dashboard. Based on our algorithm comparing similar cases in your jurisdiction, this offer ranks in the 75th percentile. Ready to discuss? Book a video call through your portal or we can hop on a quick Zoom. All documents are digitally signed and ready to go if you decide to accept.",
                "next_steps": [
                    "Review interactive settlement analysis in your portal",
                    "Use the portal's scheduling tool for a video call",
                    "Access digital signing if you decide to proceed",
                    "Get instant updates on your mobile app"
                ]
            }
        }
    
    @staticmethod
    def get_timing_examples() -> Dict[str, str]:
        """Get examples of how timing affects notification delivery."""
        
        return {
            "urgent_positive_news": "IMMEDIATE DELIVERY: 'Great news! The judge ruled in your favor!' (Sent immediately regardless of time/day)",
            
            "negative_news_friday_evening": "DELAYED: 'Unfortunately, the motion was denied...' (Delayed until Monday 9 AM to avoid weekend anxiety)",
            
            "routine_update_night": "SCHEDULED: 'Case status update...' (Scheduled for 9 AM next business day during quiet hours)",
            
            "billing_invoice": "OPTIMIZED: 'Your monthly invoice is ready' (Sent Tuesday 10 AM for better payment response rates)",
            
            "settlement_deadline": "TIME-SENSITIVE: 'Settlement response due in 2 days' (Sent immediately with follow-up reminders)"
        }
    
    @staticmethod
    def get_channel_examples() -> Dict[str, List[str]]:
        """Get examples of multi-channel notification delivery."""
        
        return {
            "urgent_settlement_deadline": [
                "Portal: Full details with document access and decision tools",
                "Email: Detailed explanation with clear deadline",
                "SMS: 'URGENT: Settlement deadline in 24 hours. Check portal for details.'",
                "Push: 'Settlement Response Due Tomorrow'",
                "Phone Call: Personal discussion if high-anxiety client"
            ],
            
            "routine_document_sharing": [
                "Portal: Document available with viewing/download options",
                "Email: 'New document shared: [title] - View in portal'"
            ],
            
            "positive_case_outcome": [
                "Portal: Comprehensive outcome details",
                "Email: Celebration message with next steps",
                "SMS: 'Great news about your case! Check your email for details.'"
            ],
            
            "payment_overdue": [
                "Portal: Payment interface with balance details",
                "Email: Friendly reminder with payment options",
                "SMS (if still overdue): 'Payment reminder - easy online payment available'"
            ]
        }


def demonstrate_notification_intelligence():
    """Demonstrate the intelligent notification system capabilities."""
    
    examples = NotificationExamples()
    personalities = PersonalizedExamples()
    
    print("=== INTELLIGENT LEGAL NOTIFICATION SYSTEM EXAMPLES ===\n")
    
    # Show complexity level examples
    print("1. COMPLEXITY LEVEL TRANSLATIONS")
    print("-" * 40)
    settlement_example = examples.get_examples_by_context(TranslationContext.SETTLEMENT_DISCUSSION)[0]
    
    print(f"Original Legal Text:\n{settlement_example.original_legal_text}\n")
    
    for level, translation in settlement_example.translated_versions.items():
        print(f"{level.value.upper()}:")
        print(f"{translation}\n")
    
    # Show personality-based personalization
    print("\n2. PERSONALITY-BASED PERSONALIZATION")
    print("-" * 40)
    personality_examples = personalities.get_personality_examples()
    
    for client_type, example in personality_examples.items():
        print(f"{client_type.upper().replace('_', ' ')}:")
        print(f"Style: {example['communication_style']}")
        print(f"Message: {example['notification'][:200]}...")
        print()
    
    # Show timing optimization
    print("\n3. TIMING OPTIMIZATION")
    print("-" * 40)
    timing_examples = personalities.get_timing_examples()
    
    for scenario, timing in timing_examples.items():
        print(f"• {timing}")
    
    # Show multi-channel delivery
    print(f"\n4. MULTI-CHANNEL DELIVERY")
    print("-" * 40)
    channel_examples = personalities.get_channel_examples()
    
    for scenario, channels in channel_examples.items():
        print(f"{scenario.upper().replace('_', ' ')}:")
        for channel in channels:
            print(f"  • {channel}")
        print()
    
    return examples


if __name__ == "__main__":
    demonstrate_notification_intelligence()