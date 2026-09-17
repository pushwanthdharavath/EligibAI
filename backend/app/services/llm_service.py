from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from app.core.config import settings

class LLMService:
    """Service for LLM-based rule extraction and explanation generation."""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM (using OpenAI as example, can be replaced with other providers)
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY
            )
        else:
            print("Warning: OPENAI_API_KEY not set. Using mock LLM responses.")
            self.llm = None
    
    def extract_eligibility_rules(self, scholarship_text: str) -> Dict[str, Any]:
        """
        Extract structured eligibility rules from scholarship text using LLM.
        
        Args:
            scholarship_text: Raw text describing scholarship eligibility
            
        Returns:
            Structured eligibility rules
        """
        if not self.llm:
            return self._mock_rule_extraction(scholarship_text)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured eligibility rules from scholarship descriptions.
Extract the following parameters if mentioned:
- education: List of eligible courses/degrees
- income_max: Maximum annual family income (in INR)
- income_min: Minimum annual family income (in INR) 
- category: List of eligible categories (SC, ST, OBC, General, EWS, etc.)
- age_min: Minimum age requirement
- age_max: Maximum age requirement
- gender: Gender requirement (Male, Female, or Any)
- state: List of eligible states
- disability_required: Whether disability certificate is required (true/false)
- year_of_study: List of eligible years of study

Return only the parameters that are explicitly mentioned in the text. 
If a parameter is not mentioned, do not include it in the output.
Return as JSON format."""),
            ("user", "Extract eligibility rules from this scholarship description:\n\n{scholarship_text}")
        ])
        
        parser = JsonOutputParser()
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({"scholarship_text": scholarship_text})
            return result
        except Exception as e:
            print(f"Error extracting rules: {e}")
            return self._mock_rule_extraction(scholarship_text)
    
    def generate_explanation(
        self, 
        user_profile: Dict[str, Any], 
        scholarship: Dict[str, Any], 
        eligibility_result: Dict[str, Any]
    ) -> str:
        """
        Generate natural language explanation of eligibility decision.
        
        Args:
            user_profile: User's profile information
            scholarship: Scholarship information
            eligibility_result: Result from eligibility engine
            
        Returns:
            Natural language explanation
        """
        if not self.llm:
            return self._generate_simple_explanation(eligibility_result)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful scholarship assistant that explains eligibility decisions clearly and accurately.
Based on the user's profile and scholarship requirements, explain why they are eligible, potentially eligible, or not eligible.
Be specific about which requirements match and which don't.
If some requirements are not specified by the scholarship, mention this clearly.
Use a friendly and encouraging tone."""),
            ("user", """User Profile:
- Name: {name}
- Education: {education}
- Year of Study: {year_of_study}
- State: {state}
- Category: {category}
- Annual Family Income: ₹{income}
- Age: {age}
- Gender: {gender}

Scholarship: {scholarship_name}
Provider: {provider}

Eligibility Analysis:
{analysis}

Overall Status: {status}

Please provide a clear explanation of this eligibility decision.""")
        ])
        
        parser = StrOutputParser()
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "name": user_profile.get("fullName", "Student"),
                "education": user_profile.get("course", "Not specified"),
                "year_of_study": user_profile.get("yearOfStudy", "Not specified"),
                "state": user_profile.get("state", "Not specified"),
                "category": user_profile.get("category", "Not specified"),
                "income": user_profile.get("annualFamilyIncome", "Not specified"),
                "age": user_profile.get("age", "Not specified"),
                "gender": user_profile.get("gender", "Not specified"),
                "scholarship_name": scholarship.get("scheme_name", "Scholarship"),
                "provider": scholarship.get("provider", "Not specified"),
                "analysis": self._format_analysis(eligibility_result),
                "status": eligibility_result.get("overall_status", "Unknown")
            })
            return result
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return self._generate_simple_explanation(eligibility_result)
    
    def answer_followup_question(
        self, 
        question: str, 
        context: List[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Answer follow-up questions about scholarships using RAG context.
        
        Args:
            question: User's follow-up question
            context: Retrieved scholarship information from RAG
            user_profile: User's profile for personalization
            
        Returns:
            Answer to the question
        """
        if not self.llm:
            return self._mock_followup_answer(question, context)
        
        # Format context
        context_text = "\n\n".join([
            f"Scholarship: {doc['metadata']['scheme_name']}\n{doc['text']}"
            for doc in context[:3]  # Use top 3 results
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a scholarship expert assistant. Answer questions about scholarships based on the provided context.
If the context doesn't contain enough information, acknowledge this and suggest where the user might find more details.
Be helpful and specific in your answers."""),
            ("user", """Question: {question}

User Profile:
- Education: {education}
- State: {state}
- Category: {category}
- Income: ₹{income}

Relevant Scholarship Information:
{context}

Please answer the question based on the provided information.""")
        ])
        
        parser = StrOutputParser()
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "question": question,
                "education": user_profile.get("course", "Not specified"),
                "state": user_profile.get("state", "Not specified"),
                "category": user_profile.get("category", "Not specified"),
                "income": user_profile.get("annualFamilyIncome", "Not specified"),
                "context": context_text
            })
            return result
        except Exception as e:
            print(f"Error answering follow-up: {e}")
            return self._mock_followup_answer(question, context)
    
    def _format_analysis(self, eligibility_result: Dict[str, Any]) -> str:
        """Format eligibility analysis for LLM prompt."""
        comparisons = eligibility_result.get("comparisons", {})
        analysis_lines = []
        
        for param, (status, reason) in comparisons.items():
            status_symbol = "✓" if status == "MATCH" else "✗" if status == "MISMATCH" else "○"
            analysis_lines.append(f"{status_symbol} {param}: {reason}")
        
        return "\n".join(analysis_lines)
    
    def _generate_simple_explanation(self, eligibility_result: Dict[str, Any]) -> str:
        """Generate simple explanation without LLM."""
        status = eligibility_result.get("overall_status", "Unknown")
        reasons = eligibility_result.get("reasons", [])
        
        if status == "Eligible":
            return f"Congratulations! You meet all the eligibility requirements for this scholarship. {', '.join(reasons)}"
        elif status == "Potentially Eligible":
            return f"You may be eligible for this scholarship. {', '.join(reasons)} Some requirements were not specified in the available information."
        else:
            return f"Unfortunately, you don't meet the eligibility requirements for this scholarship. {', '.join(reasons)}"
    
    def _mock_rule_extraction(self, scholarship_text: str) -> Dict[str, Any]:
        """Mock rule extraction when LLM is not available."""
        return {
            "education": ["B.Tech", "B.E."],
            "income_max": 500000,
            "category": ["SC", "ST"],
            "state": ["Telangana"]
        }
    
    def _mock_followup_answer(self, question: str, context: List[Dict[str, Any]]) -> str:
        """Mock follow-up answer when LLM is not available."""
        if not context:
            return "I don't have enough information to answer that question. Please provide more details or try rephrasing your question."
        
        scholarship_names = [doc['metadata']['scheme_name'] for doc in context[:3]]
        return f"Based on the available scholarships: {', '.join(scholarship_names)}. For more detailed information, please check the official scholarship websites."