from typing import List, Dict, Any, Optional
import json
from pathlib import Path

# Try to import RAGAS, fall back gracefully if not available
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
        context_entity_recall
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("RAGAS not available. Evaluation will use fallback metrics.")

class RAGASEvaluator:
    """Service for evaluating RAG system performance using RAGAS metrics."""
    
    def __init__(self):
        self.ragas_available = RAGAS_AVAILABLE
        print(f"Initializing RAGAS evaluator... (RAGAS available: {self.ragas_available})")
    
    def prepare_evaluation_dataset(
        self,
        questions: List[str],
        ground_truths: List[List[str]],
        contexts: List[List[str]],
        answers: List[str]
    ) -> Dataset:
        """
        Prepare dataset for RAGAS evaluation.
        
        Args:
            questions: List of user questions
            ground_truths: List of ground truth answers for each question
            contexts: List of retrieved contexts for each question
            answers: List of generated answers for each question
            
        Returns:
            HuggingFace Dataset for evaluation
        """
        dataset_dict = {
            "question": questions,
            "ground_truth": ground_truths,
            "contexts": contexts,
            "answer": answers
        }
        
        dataset = Dataset.from_dict(dataset_dict)
        return dataset
    
    def create_scholarship_evaluation_data(self) -> Dict[str, Any]:
        """
        Create sample evaluation data for scholarship system.
        This simulates questions, contexts, and answers for evaluation.
        """
        # Sample questions about scholarships
        questions = [
            "What scholarships are available for B.Tech students in Telangana?",
            "What is the income limit for Post-Matric Scholarship for SC students?",
            "Which scholarships are available for girl students?",
            "What documents are required for Central Sector Scheme scholarships?",
            "What is the deadline for Telangana ePASS scholarships?"
        ]
        
        # Ground truth answers (what we expect the system to return)
        ground_truths = [
            ["Telangana ePASS scholarships for SC/ST/OBC students, Central Sector Scheme, ISHAN UDAY"],
            ["Annual family income should not exceed ₹5,00,000 for SC students"],
            ["Pragati Scholarship for Girl Students, PG Indira Gandhi Scholarship for Single Girl Child"],
            ["Income Certificate, Aadhaar Card, Bank Passbook, College ID, Marksheets"],
            ["December 31, 2026 for Telangana ePASS scholarships"]
        ]
        
        # Simulated retrieved contexts (from our RAG system)
        contexts = [
            [["Post-Matric Scholarship for SC Students: B.Tech eligible, Telangana state, income ≤ ₹5L", "Central Sector Scheme: All India, income ≤ ₹2.5L", "Telangana ePASS: State-specific scholarships"]],
            [["Post-Matric Scholarship for SC Students: Income limit ₹5,00,000", "Category: SC students only", "State: Telangana"]],
            [["Pragati Scholarship: For girl students in technical courses", "PG Indira Gandhi Scholarship: For single girl child in postgraduation"]],
            [["Central Sector Scheme: Requires Income Certificate, Aadhaar Card, Bank Passbook", "College ID and Marksheets are mandatory"]],
            [["Telangana ePASS scholarships: Application deadline December 31, 2026", "Apply through official ePASS portal"]]
        ]
        
        # Simulated generated answers (from our LLM)
        answers = [
            "Based on the available information, B.Tech students in Telangana can apply for Post-Matric Scholarship for SC students through Telangana ePASS, Central Sector Scheme (all India), and ISHAN UDAY (for North Eastern region, if applicable).",
            "The Post-Matric Scholarship for SC students has an annual family income limit of ₹5,00,000. Students from SC category in Telangana are eligible.",
            "There are scholarships specifically for girl students: Pragati Scholarship for girl students in technical courses offered by AICTE, and PG Indira Gandhi Scholarship for single girl children pursuing postgraduate studies offered by UGC.",
            "The Central Sector Scheme requires several documents including Income Certificate, Aadhaar Card, Bank Passbook, College ID, and academic Marksheets. These documents need to be uploaded during the application process.",
            "The deadline for Telangana ePASS scholarships is December 31, 2026. Students should apply through the official Telangana ePASS portal before this date."
        ]
        
        return {
            "questions": questions,
            "ground_truths": ground_truths,
            "contexts": contexts,
            "answers": answers
        }
    
    def evaluate_rag_system(
        self,
        questions: List[str],
        ground_truths: List[List[str]],
        contexts: List[List[str]],
        answers: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate RAG system using RAGAS metrics.
        
        Args:
            questions: List of user questions
            ground_truths: List of ground truth answers
            contexts: List of retrieved contexts
            answers: List of generated answers
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.ragas_available:
            print("RAGAS not available, using simple evaluation...")
            return self._simple_evaluation(questions, ground_truths, contexts, answers)
        
        print("Preparing evaluation dataset...")
        dataset = self.prepare_evaluation_dataset(
            questions=questions,
            ground_truths=ground_truths,
            contexts=contexts,
            answers=answers
        )
        
        print("Running RAGAS evaluation...")
        # Define metrics to evaluate
        metrics = [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision
        ]
        
        try:
            # Run evaluation
            result = evaluate(
                dataset=dataset,
                metrics=metrics
            )
            
            # Convert to dictionary
            evaluation_results = result.to_dict()
            
            print("Evaluation completed successfully!")
            return evaluation_results
            
        except Exception as e:
            print(f"Error during evaluation: {e}")
            # Return simplified evaluation if RAGAS fails
            return self._simple_evaluation(questions, ground_truths, contexts, answers)
    
    def _simple_evaluation(
        self,
        questions: List[str],
        ground_truths: List[List[str]],
        contexts: List[List[str]],
        answers: List[str]
    ) -> Dict[str, Any]:
        """
        Simple evaluation fallback when RAGAS is not available.
        """
        print("Using simple evaluation fallback...")
        
        # Calculate basic metrics
        total_questions = len(questions)
        answer_lengths = [len(answer.split()) for answer in answers]
        context_counts = [len(ctx) for ctx in contexts]
        
        results = {
            "total_questions": total_questions,
            "avg_answer_length": sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0,
            "avg_context_count": sum(context_counts) / len(context_counts) if context_counts else 0,
            "evaluation_method": "simple_fallback",
            "message": "Full RAGAS evaluation requires additional dependencies. Using simple metrics."
        }
        
        return results
    
    def evaluate_eligibility_engine(self) -> Dict[str, Any]:
        """
        Evaluate the eligibility engine accuracy using test cases.
        
        NOTE: This function is deprecated. Static dataset has been removed.
        For evaluation, use live web search with the LangGraph orchestrator.
        """
        return {
            "status": "deprecated",
            "message": "Eligibility engine evaluation deprecated. Static dataset removed. Use live web search with /api/live-search for testing.",
            "accuracy": None,
            "test_cases": []
        }
                "expected_not_eligible": ["scholarship_003"]  # Central Sector (income too high)
            },
            {
                "profile": {
                    "fullName": "Test Student 2",
                    "age": "21",
                    "gender": "Female",
                    "state": "Telangana",
                    "district": "Hyderabad",
                    "category": "General",
                    "course": "B.Tech",
                    "yearOfStudy": "3rd Year",
                    "collegeName": "Test College",
                    "annualFamilyIncome": "200000",
                    "disabilityStatus": "No",
                    "searchQuery": "Find scholarships"
                },
                "expected_eligible": ["scholarship_006"],  # Post-Matric OBC
                "expected_not_eligible": ["scholarship_001"]  # Post-Matric SC (wrong category)
            }
        ]
        
        results = {
            "total_test_cases": len(test_cases),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, test_case in enumerate(test_cases):
            profile_dict = test_case["profile"]
            profile = UserProfile(**profile_dict)
            
            # Get all scholarships
            scholarships = dataset.get_all_scholarships()
            
            # Test each scholarship
            test_passed = True
            test_details = {
                "test_case": i + 1,
                "profile": profile_dict,
                "results": []
            }
            
            for scholarship in scholarships:
                evaluation = engine.evaluate_eligibility(scholarship, profile)
                
                # Check if results match expectations
                scholarship_id = scholarship.id
                is_eligible = evaluation["overall_status"] == "Eligible"
                
                expected_eligible = scholarship_id in test_case["expected_eligible"]
                expected_not_eligible = scholarship_id in test_case["expected_not_eligible"]
                
                if expected_eligible and not is_eligible:
                    test_passed = False
                    test_details["results"].append({
                        "scholarship": scholarship_id,
                        "expected": "Eligible",
                        "actual": evaluation["overall_status"],
                        "status": "FAIL"
                    })
                elif expected_not_eligible and is_eligible:
                    test_passed = False
                    test_details["results"].append({
                        "scholarship": scholarship_id,
                        "expected": "Not Eligible",
                        "actual": evaluation["overall_status"],
                        "status": "FAIL"
                    })
                else:
                    test_details["results"].append({
                        "scholarship": scholarship_id,
                        "expected": "Any",
                        "actual": evaluation["overall_status"],
                        "status": "PASS"
                    })
            
            if test_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(test_details)
        
        results["accuracy"] = results["passed"] / results["total_test_cases"] if results["total_test_cases"] > 0 else 0
        
        return results
    
    def generate_evaluation_report(self, rag_results: Dict[str, Any], eligibility_results: Dict[str, Any]) -> str:
        """Generate a comprehensive evaluation report."""
        report = []
        report.append("=" * 50)
        report.append("ELIGIBAI SYSTEM EVALUATION REPORT")
        report.append("=" * 50)
        report.append("")
        
        # RAG Evaluation Results
        report.append("RAG SYSTEM EVALUATION")
        report.append("-" * 30)
        if "faithfulness" in rag_results:
            report.append(f"Faithfulness: {rag_results.get('faithfulness', 'N/A'):.3f}")
            report.append(f"Answer Relevancy: {rag_results.get('answer_relevancy', 'N/A'):.3f}")
            report.append(f"Context Recall: {rag_results.get('context_recall', 'N/A'):.3f}")
            report.append(f"Context Precision: {rag_results.get('context_precision', 'N/A'):.3f}")
        else:
            report.append(f"Total Questions: {rag_results.get('total_questions', 0)}")
            report.append(f"Average Answer Length: {rag_results.get('avg_answer_length', 0):.2f} words")
            report.append(f"Average Context Count: {rag_results.get('avg_context_count', 0):.2f}")
            report.append(f"Method: {rag_results.get('evaluation_method', 'unknown')}")
        
        report.append("")
        
        # Eligibility Engine Results
        report.append("ELIGIBILITY ENGINE EVALUATION")
        report.append("-" * 30)
        report.append(f"Total Test Cases: {eligibility_results.get('total_test_cases', 0)}")
        report.append(f"Passed: {eligibility_results.get('passed', 0)}")
        report.append(f"Failed: {eligibility_results.get('failed', 0)}")
        report.append(f"Accuracy: {eligibility_results.get('accuracy', 0):.2%}")
        
        report.append("")
        report.append("=" * 50)
        report.append("EVALUATION COMPLETE")
        report.append("=" * 50)
        
        return "\n".join(report)

def run_full_evaluation():
    """Run complete system evaluation."""
    evaluator = RAGASEvaluator()
    
    print("Running RAG evaluation...")
    rag_data = evaluator.create_scholarship_evaluation_data()
    rag_results = evaluator.evaluate_rag_system(
        questions=rag_data["questions"],
        ground_truths=rag_data["ground_truths"],
        contexts=rag_data["contexts"],
        answers=rag_data["answers"]
    )
    
    print("Running eligibility engine evaluation...")
    eligibility_results = evaluator.evaluate_eligibility_engine()
    
    print("Generating evaluation report...")
    report = evaluator.generate_evaluation_report(rag_results, eligibility_results)
    print(report)
    
    # Save report to file
    report_path = Path("evaluation_report.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Evaluation report saved to {report_path}")
    
    return {
        "rag_results": rag_results,
        "eligibility_results": eligibility_results,
        "report": report
    }

if __name__ == "__main__":
    print("Starting EligibAI system evaluation...")
    run_full_evaluation()