"""
Demandify Caller Agent - Enhanced Dynamic Cold Calling System
Author: Demandify Media
Campaign: SplashBI Unified Oracle Reporting Solutions
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CallStage(Enum):
    GREETING = "greeting"
    PERMISSION = "permission"
    QUALIFICATION = "qualification"
    VALUE_PITCH = "value_pitch"
    DISCOVERY_CQ1 = "discovery_cq1"
    DISCOVERY_CQ1A = "discovery_cq1a"
    DISCOVERY_CQ1B = "discovery_cq1b"
    DISCOVERY_CQ2 = "discovery_cq2"
    DISCOVERY_CQ3 = "discovery_cq3"
    EMAIL_CONFIRMATION = "email_confirmation"
    CLOSING = "closing"
    ENDED = "ended"


class ResponseSentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    OBJECTION = "objection"
    QUESTION = "question"
    INTERRUPTION = "interruption"


@dataclass
class ProspectData:
    name: str
    company: str
    job_title: str
    email: str
    phone: str = ""
    industry: str = ""
    additional_notes: str = ""


class DemandifyCallerAgent:
    """
    Enhanced AI Cold Calling Agent for B2B SplashBI Campaign
    Handles dynamic responses and maintains natural conversation flow
    """
    
    def __init__(self):
        self.current_stage = CallStage.GREETING
        self.conversation_history = []
        self.prospect_data = None
        self.objection_count = 0
        self.rapport_level = 0  # -5 to 5 scale
        self.prospect_personality = "neutral"  # chatty, brief, skeptical, professional
        
        # Initialize response templates
        self._init_response_templates()
        self._init_objection_handlers()
        self._init_transition_phrases()
    
    def _init_response_templates(self):
        """Initialize all dynamic response templates"""
        
        self.greeting_responses = {
            ResponseSentiment.POSITIVE: [
                "That's wonderful to hear.",
                "Glad to catch you on a good day.",
                "Perfect.",
                "That's great."
            ],
            ResponseSentiment.NEGATIVE: [
                "I understand—we all have those days.",
                "I appreciate your honesty.",
                "I hear you.",
                "Sorry to hear that."
            ],
            ResponseSentiment.NEUTRAL: [
                "Thanks for taking my call.",
                "I appreciate you picking up.",
                "Thank you."
            ]
        }
        
        self.permission_requests = [
            "I know you're busy, so is now a good time for just a few minutes?",
            "Would you have about 3-4 minutes to chat?",
            "I promise to be brief—do you have a moment?",
            "Could I have just a few minutes of your time?"
        ]
        
        self.permission_responses = {
            ResponseSentiment.POSITIVE: [
                "Great, thank you.",
                "Perfect, I appreciate it.",
                "Wonderful.",
                "Excellent."
            ],
            "conditional": [
                "Absolutely, I'll be brief.",
                "Of course, just a few minutes.",
                "I respect your time—this will be quick.",
                "Perfect, I'll keep this short."
            ],
            ResponseSentiment.NEGATIVE: [
                "I completely understand. When would be a better time to reach you?",
                "No problem at all. What day this week works better?",
                "Of course. Should I try back tomorrow morning or afternoon?",
                "That's fine. When would be more convenient?"
            ]
        }
        
        self.qualification_responses = {
            "correct": [
                "Perfect, thank you.",
                "Great, I have the right person.",
                "Excellent.",
                "That's right."
            ],
            "correction": [
                "Got it, thanks for the clarification.",
                "Perfect, I'll make note of that.",
                "Appreciate the correction.",
                "Thank you for updating me."
            ],
            "wrong_person": [
                "Thanks for letting me know. Who would be the best person to speak with about Oracle reporting and BI initiatives?",
                "I understand. Could you point me to the right person on your team?",
                "Got it. Who handles Oracle reporting decisions there?"
            ]
        }
    
    def _init_objection_handlers(self):
        """Initialize comprehensive objection handling responses"""
        
        self.objection_handlers = {
            "budget": {
                "no_budget": [
                    "I totally get that. This is just an exploration call—no commitments. If there's value, we can discuss timing that works.",
                    "Makes sense. That's exactly why this discovery call is helpful—to see if the ROI justifies future budget.",
                    "I understand budget constraints. Many clients started this conversation the same way."
                ],
                "not_in_cycle": [
                    "Perfect timing then—this gives you information for your next cycle.",
                    "That's actually ideal. We can explore the value now and align with your planning timeline.",
                    "Great point. This conversation helps you prepare for when the budget opens up."
                ]
            },
            "time": {
                "too_busy": [
                    "I completely understand. That's actually why SplashBI exists—to give busy professionals like you time back.",
                    "I hear you. When things calm down, having better reporting tools becomes even more valuable.",
                    "Makes total sense. What about next week—would Tuesday or Wednesday afternoon work better?"
                ],
                "in_middle": [
                    "Of course, I can hear you're focused. Should I call back in an hour or later today?",
                    "I understand—bad timing on my part. Tomorrow morning or afternoon better?",
                    "No problem at all. When would be a better time to connect?"
                ]
            },
            "trust": {
                "sales_call": [
                    "I get it—you probably get a lot of these. I'm actually trying to save you time by connecting you directly with someone who can show real value.",
                    "Fair point. I'm not here to pitch you today—just to see if a conversation with our expert makes sense.",
                    "I understand. That's why I want to connect you with someone who can actually help, not just talk."
                ],
                "how_got_number": [
                    "We research companies using Oracle systems who might benefit from better reporting. Your name came up as someone involved in these initiatives.",
                    "Good question. We identify professionals at Oracle shops who might find value in our platform.",
                    "We focus on Oracle users who might benefit from streamlined reporting solutions."
                ]
            },
            "competition": {
                "have_solution": [
                    "That's great—many of our clients actually use both solutions for different purposes.",
                    "Good choice. The question is whether you're getting everything you need from it.",
                    "Interesting. Most teams find SplashBI complements their existing tools nicely."
                ]
            },
            "interest": {
                "not_interested": [
                    "I appreciate your directness. Let me ask—what if I told you this could cut your monthly reporting time by 60%?",
                    "I understand. Many felt the same way before seeing the demo. What's your biggest reporting headache right now?",
                    "Fair enough. Even just learning what's possible might be valuable for future reference."
                ],
                "send_info": [
                    "Absolutely, I'll email over a short overview. While I have you, could we pencil 15 minutes with the SME so the material is most relevant?",
                    "Of course. I find the information is most valuable when you can ask questions directly. How about a brief call next week?",
                    "Sure thing. The material really comes to life in a conversation though—would a quick call make sense?"
                ]
            }
        }
    
    def _init_transition_phrases(self):
        """Initialize natural conversation transition phrases"""
        
        self.transition_phrases = [
            "You know what...",
            "Here's the thing...",
            "Let me ask you this...",
            "I'm curious...",
            "That's interesting...",
            "Fair enough...",
            "I hear you...",
            "That makes total sense..."
        ]
        
        self.acknowledgment_phrases = [
            "I appreciate that.",
            "That's fair.",
            "I understand.",
            "Good point.",
            "I can see that.",
            "That's reasonable.",
            "Makes sense.",
            "I hear you."
        ]
        
        self.rapport_builders = [
            "You're absolutely right about that.",
            "That's exactly what I hear from other Oracle users.",
            "You're definitely not alone in that challenge.",
            "That sounds frustrating.",
            "I can relate to that.",
            "That's a common concern."
        ]
    
    def analyze_response_sentiment(self, user_input: str) -> ResponseSentiment:
        """Analyze user response to determine sentiment and intent"""
        
        user_input_lower = user_input.lower()
        
        # Objection patterns
        objection_patterns = [
            r'\bnot interested\b', r'\bdont? need\b', r'\balready have\b',
            r'\bno budget\b', r'\btoo expensive\b', r'\bbad time\b',
            r'\btoo busy\b', r'\bsend.*info\b', r'\bemail.*me\b'
        ]
        
        if any(re.search(pattern, user_input_lower) for pattern in objection_patterns):
            return ResponseSentiment.OBJECTION
        
        # Question patterns
        if '?' in user_input or any(word in user_input_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            return ResponseSentiment.QUESTION
        
        # Positive patterns
        positive_words = ['good', 'great', 'fine', 'yes', 'sure', 'okay', 'sounds good', 'interested']
        if any(word in user_input_lower for word in positive_words):
            return ResponseSentiment.POSITIVE
        
        # Negative patterns  
        negative_words = ['no', 'not really', 'bad', 'terrible', 'awful', 'busy', 'rough']
        if any(word in user_input_lower for word in negative_words):
            return ResponseSentiment.NEGATIVE
        
        return ResponseSentiment.NEUTRAL
    
    def detect_personality_type(self, user_input: str):
        """Detect prospect's communication style for adaptive responses"""
        
        word_count = len(user_input.split())
        
        if word_count > 20:
            self.prospect_personality = "chatty"
        elif word_count < 5:
            self.prospect_personality = "brief"
        elif any(word in user_input.lower() for word in ['skeptical', 'doubt', 'not sure', 'prove']):
            self.prospect_personality = "skeptical"
        else:
            self.prospect_personality = "professional"
    
    def get_dynamic_response(self, user_input: str, lead_context: ProspectData = None) -> str:
        """Generate dynamic response based on current stage and user input"""
        
        if lead_context:
            self.prospect_data = lead_context
        
        sentiment = self.analyze_response_sentiment(user_input)
        self.detect_personality_type(user_input)
        
        # Log conversation
        self.conversation_history.append({
            'stage': self.current_stage.value,
            'user_input': user_input,
            'sentiment': sentiment.value,
            'personality': self.prospect_personality
        })
        
        # Route to appropriate handler
        if self.current_stage == CallStage.GREETING:
            return self._handle_greeting_response(user_input, sentiment)
        elif self.current_stage == CallStage.PERMISSION:
            return self._handle_permission_response(user_input, sentiment)
        elif self.current_stage == CallStage.QUALIFICATION:
            return self._handle_qualification_response(user_input, sentiment)
        elif self.current_stage == CallStage.VALUE_PITCH:
            return self._handle_value_pitch_response(user_input, sentiment)
        elif self.current_stage in [CallStage.DISCOVERY_CQ1, CallStage.DISCOVERY_CQ1A, 
                                   CallStage.DISCOVERY_CQ1B, CallStage.DISCOVERY_CQ2, 
                                   CallStage.DISCOVERY_CQ3]:
            return self._handle_discovery_response(user_input, sentiment)
        elif self.current_stage == CallStage.EMAIL_CONFIRMATION:
            return self._handle_email_response(user_input, sentiment)
        elif self.current_stage == CallStage.CLOSING:
            return self._handle_closing_response(user_input, sentiment)
        else:
            return self._handle_general_objection(user_input, sentiment)
    
    def _handle_greeting_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle response to greeting"""
        
        if sentiment == ResponseSentiment.OBJECTION:
            return self._handle_general_objection(user_input, sentiment)
        
        # Get appropriate greeting response
        response_options = self.greeting_responses.get(sentiment, self.greeting_responses[ResponseSentiment.NEUTRAL])
        greeting_response = random.choice(response_options)
        
        # Move to permission request
        permission_request = random.choice(self.permission_requests)
        self.current_stage = CallStage.PERMISSION
        
        return f"{greeting_response} {permission_request}"
    
    def _handle_permission_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle response to permission request"""
        
        if sentiment == ResponseSentiment.NEGATIVE or "no" in user_input.lower():
            response = random.choice(self.permission_responses[ResponseSentiment.NEGATIVE])
            self.current_stage = CallStage.ENDED
            return response
        
        if any(phrase in user_input.lower() for phrase in ["quick", "brief", "short", "make it fast"]):
            response = random.choice(self.permission_responses["conditional"])
        else:
            response = random.choice(self.permission_responses[ResponseSentiment.POSITIVE])
        
        # Move to qualification
        self.current_stage = CallStage.QUALIFICATION
        qualification = f"I believe you're the {self.prospect_data.job_title} at {self.prospect_data.company}, is that correct?"
        
        return f"{response} {qualification}"
    
    def _handle_qualification_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle response to qualification"""
        
        if "yes" in user_input.lower() or "correct" in user_input.lower():
            response = random.choice(self.qualification_responses["correct"])
        elif any(word in user_input.lower() for word in ["actually", "no", "wrong"]):
            response = random.choice(self.qualification_responses["correction"])
        else:
            response = random.choice(self.qualification_responses["correct"])
        
        # Move to value pitch
        self.current_stage = CallStage.VALUE_PITCH
        value_pitch = ("The reason for my call is to schedule a short conversation with a subject matter expert "
                      "from SplashBI to explore how we're helping companies modernize Oracle reporting across "
                      "EBS, Fusion Cloud, and EPM—with a platform that enables real-time access, "
                      "planning-to-actuals integration, and self-service reporting across teams. "
                      "We're looking to arrange a quick session either next week or the week after. Would that work for you?")
        
        return f"{response} {value_pitch}"
    
    def _handle_value_pitch_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle response to value pitch"""
        
        if sentiment == ResponseSentiment.OBJECTION:
            return self._handle_general_objection(user_input, sentiment)
        
        if sentiment == ResponseSentiment.POSITIVE:
            response = random.choice(["I'm glad it resonates.", "That's great to hear.", "Perfect."])
        else:
            response = random.choice(["I understand.", "That makes sense.", "Fair enough."])
        
        # Move to discovery
        self.current_stage = CallStage.DISCOVERY_CQ1
        discovery_q1 = "What are your current challenges with Oracle reporting or BI tools?"
        
        return f"{response} {discovery_q1}"
    
    def _handle_discovery_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle discovery question responses"""
        
        if sentiment == ResponseSentiment.OBJECTION:
            return self._handle_general_objection(user_input, sentiment)
        
        # Acknowledge their response
        acknowledgment = random.choice(self.rapport_builders)
        
        # Progress through discovery stages
        if self.current_stage == CallStage.DISCOVERY_CQ1:
            self.current_stage = CallStage.DISCOVERY_CQ1A
            next_q = "Do you have enough resources to support the business?"
        elif self.current_stage == CallStage.DISCOVERY_CQ1A:
            self.current_stage = CallStage.DISCOVERY_CQ1B
            next_q = "Could you identify your most immediate pain areas? Manual processes delaying close cycles, lack of unified data, or reliance on outdated tools?"
        elif self.current_stage == CallStage.DISCOVERY_CQ1B:
            self.current_stage = CallStage.DISCOVERY_CQ2
            next_q = "When it comes to evaluating solutions like this, what role do you typically play in the decision-making process?"
        elif self.current_stage == CallStage.DISCOVERY_CQ2:
            self.current_stage = CallStage.DISCOVERY_CQ3
            next_q = "If this solution resonates with your team, what's your typical evaluation timeframe—1-3 months, 3-6 months, or 6-9 months?"
        else:  # CQ3
            self.current_stage = CallStage.EMAIL_CONFIRMATION
            next_q = (f"While we're setting up the call, I'd also like to send you a quick overview titled: "
                     f"'SplashBI for Oracle Reporting.' It outlines how we help organizations streamline reporting "
                     f"across Oracle EBS, Fusion Cloud, and EPM. I have your email as {self.prospect_data.email}, is that correct?")
        
        return f"{acknowledgment} {next_q}"
    
    def _handle_email_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle email confirmation response"""
        
        if "yes" in user_input.lower() or "correct" in user_input.lower():
            response = random.choice(["Perfect.", "Great, I have it right."])
        else:
            response = random.choice(["Got it, let me update that.", "Thanks for the correction."])
        
        # Move to closing
        self.current_stage = CallStage.CLOSING
        closing = ("Perfect! A team member from SplashBI will follow up with you next week or the week after. "
                  "Thanks again for your time—I'll share the details shortly.")
        
        return f"{response} {closing}"
    
    def _handle_closing_response(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle closing responses"""
        
        if sentiment == ResponseSentiment.POSITIVE:
            response = "Excellent. You'll hear from our team within 48 hours."
        else:
            response = "Absolutely. How about I have them follow up next week? If you're not interested then, just let them know."
        
        self.current_stage = CallStage.ENDED
        return response
    
    def _handle_general_objection(self, user_input: str, sentiment: ResponseSentiment) -> str:
        """Handle general objections with dynamic responses"""
        
        user_lower = user_input.lower()
        
        # Budget objections
        if any(phrase in user_lower for phrase in ["budget", "expensive", "cost", "money"]):
            if "no budget" in user_lower:
                return random.choice(self.objection_handlers["budget"]["no_budget"])
            else:
                return random.choice(self.objection_handlers["budget"]["not_in_cycle"])
        
        # Time objections
        elif any(phrase in user_lower for phrase in ["busy", "time", "rush"]):
            if "too busy" in user_lower:
                return random.choice(self.objection_handlers["time"]["too_busy"])
            else:
                return random.choice(self.objection_handlers["time"]["in_middle"])
        
        # Trust/skepticism objections
        elif any(phrase in user_lower for phrase in ["sales call", "not interested", "skeptical"]):
            return random.choice(self.objection_handlers["trust"]["sales_call"])
        
        # Competition objections
        elif any(phrase in user_lower for phrase in ["already have", "using", "current solution"]):
            return random.choice(self.objection_handlers["competition"]["have_solution"])
        
        # Interest objections
        elif "send info" in user_lower or "email me" in user_lower:
            return random.choice(self.objection_handlers["interest"]["send_info"])
        elif "not interested" in user_lower:
            return random.choice(self.objection_handlers["interest"]["not_interested"])
        
        # Default acknowledgment
        return f"{random.choice(self.acknowledgment_phrases)} {random.choice(self.transition_phrases)} let me ask you this—what's your biggest reporting challenge right now?"
    
    def initiate_call(self, lead_context: ProspectData) -> str:
        """Start the cold call with personalized greeting"""
        
        self.prospect_data = lead_context
        self.current_stage = CallStage.GREETING
        
        greeting = f"Hi {lead_context.name}, this is [Agent Name] from DemandTeq on behalf of SplashBI, how are you today?"
        
        return greeting
    
    def get_call_summary(self) -> Dict:
        """Generate summary of the call for reporting"""
        
        return {
            "final_stage": self.current_stage.value,
            "conversation_length": len(self.conversation_history),
            "objection_count": self.objection_count,
            "rapport_level": self.rapport_level,
            "prospect_personality": self.prospect_personality,
            "outcome": "qualified" if self.current_stage == CallStage.ENDED else "in_progress"
        }


# Example Usage and Testing
if __name__ == "__main__":
    
    # Sample prospect data
    sample_prospect = ProspectData(
        name="John Smith",
        company="ABC Corporation",
        job_title="IT Director",
        email="john.smith@abc.com"
    )
    
    # Initialize agent
    agent = DemandifyCallerAgent()
    
    # Start call
    print("=== DEMANDIFY CALLER AGENT DEMO ===\n")
    initial_greeting = agent.initiate_call(sample_prospect)
    print(f"Agent: {initial_greeting}")
    
    # Simulate conversation
    test_responses = [
        "I'm doing well, thanks.",
        "Sure, I have a few minutes.",
        "Yes, that's correct.",
        "We're struggling with slow reporting and too much manual work.",
        "Not really, we're understaffed.",
        "Manual processes are killing us.",
        "I'm the decision maker.",
        "Probably 3-6 months.",
        "Yes, that email is right."
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\nProspect: {response}")
        agent_response = agent.get_dynamic_response(response, sample_prospect)
        print(f"Agent: {agent_response}")
        
        if agent.current_stage == CallStage.ENDED:
            break
    
    print(f"\n=== CALL SUMMARY ===")
    summary = agent.get_call_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")