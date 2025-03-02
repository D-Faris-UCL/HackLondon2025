from sentence_transformers import SentenceTransformer, util
import re
import asyncio

import time

# Load a pre-trained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def check(original, markdown):
    matches = [m.group(1) for m in re.finditer(r'"(.*?)"', markdown)]
    filtered_quotes = [quote for quote in matches if len(quote) >= 50]
    
    count = 0
    start_position = 0
    for quote in filtered_quotes:
        if "..." in quote:
            count+=1
            continue
        quote_embedding = model.encode(quote, convert_to_tensor=True)
        window_size = int(len(quote) * 1.5)
        step_size = int(len(quote) * 1)

        steps_needed = len(original) // step_size + 1
        for i in range(steps_needed):
            current_start = (start_position + i * step_size) % len(original)
            window = ""
            
            if current_start + window_size <= len(original):
                # Simple case - window fits within remaining text
                window = original[current_start:current_start + window_size]
            else:
                # Wrap-around case - window spans end and beginning
                end_part = original[current_start:]
                start_part = original[:window_size - len(end_part)]
                window = end_part + start_part

            window_embedding = model.encode(window, convert_to_tensor=True)

            similarity = util.pytorch_cos_sim(window_embedding, quote_embedding).item()
            if similarity > 0.75:
                count += 1
                start_position = current_start
                break
    return count >= len(filtered_quotes) - 1


