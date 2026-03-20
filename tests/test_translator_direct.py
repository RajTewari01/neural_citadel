from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

MODEL_PATH = r"D:\neural_citadel\assets\models\language_translation\nllb-200-distilled-600M"

def test_direct():
    print(f"Loading model from {MODEL_PATH}...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
        
        # English to Hindi (hin_Deva)
        translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang='eng_Latn', tgt_lang='hin_Deva')
        
        text = "Artificial Intelligence is transforming the future of humanity."
        print(f"\nOriginal: {text}")
        
        res = translator(text)
        print(f"Hindi: {res[0]['translation_text']}")
        
        # English to Bengali (ben_Beng)
        translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang='eng_Latn', tgt_lang='ben_Beng')
        res = translator(text)
        print(f"Bengali: {res[0]['translation_text']}")
        
        print("\n[SUCCESS] Model is working!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    test_direct()
