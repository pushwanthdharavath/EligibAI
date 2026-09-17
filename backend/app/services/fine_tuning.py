import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
from typing import List, Dict, Any
import json
from pathlib import Path
import os

class QLoRATrainer:
    """Service for fine-tuning LLMs using QLoRA (Quantized Low-Rank Adaptation)."""
    
    def __init__(self, base_model: str = "Qwen/Qwen2.5-3B-Instruct"):
        self.base_model = base_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
    def prepare_training_data(self, scholarship_data: List[Dict[str, Any]]) -> Dataset:
        """
        Prepare training data from scholarship information for fine-tuning.
        Focus on government terminology and eligibility rule extraction.
        """
        training_examples = []
        
        for scholarship in scholarship_data:
            # Handle scholarship data structure
            if isinstance(scholarship, dict):
                eligibility = scholarship.get('eligibility', {})
                scheme_name = scholarship.get('scheme_name', 'Unknown')
                provider = scholarship.get('provider', 'Unknown')
                benefit = scholarship.get('benefit', 'Not specified')
                deadline = scholarship.get('deadline', 'Not specified')
                state = scholarship.get('state', 'India')
            else:
                # Assume it's an object with attributes
                eligibility = scholarship.eligibility.model_dump() if hasattr(scholarship, 'eligibility') else {}
                scheme_name = scholarship.scheme_name if hasattr(scholarship, 'scheme_name') else 'Unknown'
                provider = scholarship.provider if hasattr(scholarship, 'provider') else 'Unknown'
                benefit = scholarship.benefit if hasattr(scholarship, 'benefit') else 'Not specified'
                deadline = scholarship.deadline if hasattr(scholarship, 'deadline') else 'Not specified'
                state = scholarship.state if hasattr(scholarship, 'state') else 'India'
            
            # Create various training examples for different tasks
            
            # Task 1: Eligibility rule extraction
            example_1 = {
                "input": f"Extract eligibility rules from this scholarship description:\n\nScholarship: {scheme_name}\nProvider: {provider}\nEligibility: Education: {', '.join(eligibility.get('education', []))}, Income: {eligibility.get('income_max', 'Not specified')}, Category: {', '.join(eligibility.get('category', []))}",
                "output": json.dumps({
                    "education": eligibility.get('education', []),
                    "income_max": eligibility.get('income_max'),
                    "category": eligibility.get('category', []),
                    "state": eligibility.get('state', [])
                })
            }
            training_examples.append(example_1)
            
            # Task 2: Scholarship matching
            education_list = eligibility.get('education', ['B.Tech'])
            education_str = education_list[0] if education_list else 'B.Tech'
            income_limit = eligibility.get('income_max', 500000)
            
            example_2 = {
                "input": f"A student is studying {education_str} in {state} with income ₹{income_limit}. Which scholarships might they be eligible for?",
                "output": f"Based on the profile, the student may be eligible for {scheme_name} from {provider}. Key requirements: {', '.join(eligibility.get('education', []))}, income ≤ ₹{income_limit}."
            }
            training_examples.append(example_2)
            
            # Task 3: Benefit explanation
            example_3 = {
                "input": f"What are the benefits and deadline for {scheme_name}?",
                "output": f"The {scheme_name} from {provider} offers {benefit}. The application deadline is {deadline}."
            }
            training_examples.append(example_3)
        
        # Convert to HuggingFace Dataset format
        dataset = Dataset.from_list(training_examples)
        return dataset
    
    def setup_model_and_tokenizer(self):
        """Load base model and tokenizer for QLoRA fine-tuning."""
        print(f"Loading model: {self.base_model}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            load_in_8bit=True if self.device == "cuda" else False
        )
        
        # Prepare model for k-bit training
        model = prepare_model_for_kbit_training(model)
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Apply LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        return model, tokenizer
    
    def tokenize_function(self, examples, tokenizer):
        """Tokenize training examples."""
        # Format examples as instruction-following
        formatted_texts = []
        for input_text, output_text in zip(examples["input"], examples["output"]):
            formatted_text = f"### Instruction:\n{input_text}\n\n### Response:\n{output_text}"
            formatted_texts.append(formatted_text)
        
        # Tokenize
        tokenized = tokenizer(
            formatted_texts,
            truncation=True,
            max_length=512,
            padding="max_length",
            return_tensors=None
        )
        
        return tokenized
    
    def fine_tune(
        self,
        training_data: List[Dict[str, Any]],
        output_dir: str = "./fine_tuned_model",
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4
    ):
        """
        Fine-tune the model using QLoRA.
        
        Args:
            training_data: List of training examples
            output_dir: Directory to save the fine-tuned model
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate for training
        """
        print("Starting QLoRA fine-tuning...")
        
        # Prepare dataset
        dataset = self.prepare_training_data(training_data)
        
        # Setup model and tokenizer
        model, tokenizer = self.setup_model_and_tokenizer()
        
        # Tokenize dataset
        tokenized_dataset = dataset.map(
            lambda x: self.tokenize_function(x, tokenizer),
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Split into train and validation
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=1,
            learning_rate=learning_rate,
            fp16=True if self.device == "cuda" else False,
            logging_steps=10,
            save_steps=100,
            save_total_limit=2,
            evaluation_strategy="steps",
            eval_steps=100,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="none"  # Disable wandb/mlflow for simplicity
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=split_dataset["train"],
            eval_dataset=split_dataset["test"],
            data_collator=data_collator,
        )
        
        # Start training
        print("Starting training...")
        trainer.train()
        
        # Save model
        print(f"Saving fine-tuned model to {output_dir}")
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        print("Fine-tuning completed successfully!")
        return output_dir
    
    def load_fine_tuned_model(self, model_path: str):
        """Load a fine-tuned model for inference."""
        print(f"Loading fine-tuned model from {model_path}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        return model, tokenizer
    
    def generate_response(self, model, tokenizer, prompt: str, max_length: int = 256):
        """Generate response using fine-tuned model."""
        formatted_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n"
        
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=0.7,
                do_sample=True,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the response part
        if "### Response:" in response:
            response = response.split("### Response:")[-1].strip()
        
        return response

if __name__ == "__main__":
    # Example usage
    print("Creating QLoRA trainer...")
    trainer = QLoRATrainer()
    
    print("Preparing training data...")
    # Load training data from external source to avoid circular imports
    import json
    training_data_path = Path(__file__).parent.parent.parent / "data" / "scholarships.json"
    
    if training_data_path.exists():
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)
    else:
        print(f"Training data not found at {training_data_path}")
        training_data = []
    
    print(f"Training with {len(training_data)} scholarship examples...")
    
    # Note: This requires GPU for practical training
    # For demonstration, we'll skip actual training but show the setup
    print("To run actual fine-tuning, ensure you have GPU access and run:")
    print("trainer.fine_tune(training_data, output_dir='./fine_tuned_scholarship_model')")