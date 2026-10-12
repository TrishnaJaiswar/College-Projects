import os
import shutil

model_path = os.path.abspath("NLP/models/whisper_safetensors_backup")
output_path = os.path.abspath("NLP/models/whisper_small_ct2")

print(f"Input:  {model_path}")
print(f"Output: {output_path}")

# Verify it's whisper-small
import json
with open(os.path.join(model_path, "config.json")) as f:
    cfg = json.load(f)
print(f"Model: {cfg.get('model_type')} | Layers: {cfg.get('num_hidden_layers')} | d_model: {cfg.get('d_model')}")
print("Converting whisper-small to CTranslate2 int8...")

try:
    from ctranslate2.converters import TransformersConverter
    converter = TransformersConverter(model_path)
    converter.convert(output_path, quantization="int8", force=True)

    size = sum(
        os.path.getsize(os.path.join(output_path, f))
        for f in os.listdir(output_path)
    )
    print(f"\nConversion done! Total size: {size // (1024*1024)} MB")
    for f in os.listdir(output_path):
        sz = os.path.getsize(os.path.join(output_path, f))
        print(f"  {f}: {sz // 1024} KB")

    # Replace whisper folder
    whisper_dir = os.path.abspath("NLP/models/whisper")
    if os.path.exists(whisper_dir):
        shutil.rmtree(whisper_dir)
    shutil.copytree(output_path, whisper_dir)
    shutil.rmtree(output_path)
    print("\nDone! NLP/models/whisper now has fine-tuned whisper-small.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()