from datasets import load_dataset
import os
import re

path_to_script = os.path.dirname(os.path.abspath(__file__))


DATASET_PATH = os.path.join(path_to_script, "dataset.txt")
ALLOWED_CHARS = "1234567890ß!\"$%&/()=?'+#-.,*'_:;<>|{[]}\\~@€^`qwertzuiopüasdfghjklöäyxcvbnmQWERTZUIOPÜASDFGHJKLÖÄYXCVBNM \n"


def save_dataset_to_file(filename: str, num_samples):
    ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
    allowed_chars_regex = re.compile(f"[^{re.escape(ALLOWED_CHARS)}]")

    with open(filename, "w", encoding="utf-8") as f:
        count = 0
        for sample in iter(ds):
            code = sample["code"]
            if allowed_chars_regex.search(code):
                continue
            f.write(code)
            count += 1
            if count >= num_samples:
                break

    print(f"Saved {count} code samples to {filename}")


if not os.path.exists(DATASET_PATH):
    save_dataset_to_file(DATASET_PATH, 10000)
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = f.read().lower()

if __name__ == "__main__":
    chars = set(dataset)
    my_chars = "1234567890ß!\"$%&/()=?'+#-.,*'_:;<>|{[]}\\~@€^`qwertzuiopüasdfghjklöäyxcvbnmQWERTZUIOPÜASDFGHJKLÖÄYXCVBNM \n"
    print(f"Unique characters in dataset: {len(chars)}")
    print(f"Characters present in the dataset: {''.join(sorted(chars))}")
    print(
        f"Allowed characters not in the dataset: {''.join(sorted(set(my_chars) - chars))}"
    )
    print(
        f"Characters in the dataset but not allowed: {''.join(sorted(chars - set(my_chars)))}"
    )
