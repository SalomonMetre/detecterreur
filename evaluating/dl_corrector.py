import transformers
from transformers import AutoTokenizer, AutoModel1ForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("PoloHuggingface/French_grammar_error_corrector")
model = AutoModelForSeq2SeqLM.from_pretrained("PoloHuggingface/French_grammar_error_corrector")