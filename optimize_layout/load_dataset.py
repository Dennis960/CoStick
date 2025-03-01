from datasets import load_dataset
import os
import re

path_to_script = os.path.dirname(os.path.abspath(__file__))


DATASET_PATH = os.path.join(path_to_script, "dataset.txt")
ALLOWED_CHARS = "1234567890ß!\"$%&/()=?'+#-.,*'_:;<>|{[]}\\~@€^`°qwertzuiopüasdfghjklöäyxcvbnmQWERTZUIOPÜASDFGHJKLÖÄYXCVBNM \n\t"
IGNORED_CHARS = "€~^\t"
NEEDED_CHARS = set(set(ALLOWED_CHARS.lower()) - set(IGNORED_CHARS))


def save_dataset_to_file(filename: str):
    ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
    allowed_chars_regex = re.compile(f"[^{re.escape(ALLOWED_CHARS)}]")
    found_chars = set()
    sample_count = 0

    with open(filename, "w", encoding="utf-8") as f:
        for sample in iter(ds):
            code = sample["code"]
            if allowed_chars_regex.search(code):
                continue
            f.write(code)
            new_char = set(code) - found_chars
            if new_char:
                still_missing_chars = NEEDED_CHARS - found_chars
                print(f"Missing: {still_missing_chars}")
                found_chars |= new_char
            sample_count += 1
            if found_chars >= NEEDED_CHARS:
                break
        # get sample_count samples to double the dataset size
        for sample in iter(ds):
            code = sample["code"]
            if allowed_chars_regex.search(code):
                continue
            f.write(code)
            sample_count -= 1
            if sample_count == 0:
                break

    print(f"Saved {sample_count} code samples to {filename}")


if not os.path.exists(DATASET_PATH):
    save_dataset_to_file(DATASET_PATH)
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = f.read().lower()

if __name__ == "__main__":
    chars = set(dataset)
    my_chars = ALLOWED_CHARS.lower()
    print(f"Unique characters in dataset: {len(chars)}")
    print(f"Characters present in the dataset: {''.join(sorted(chars))}")
    print(
        f"Allowed characters not in the dataset: {''.join(sorted(set(my_chars) - chars))}"
    )
    print(
        f"Characters in the dataset but not allowed: {''.join(sorted(chars - set(my_chars)))}"
    )
    # count number of not allowed characters

    not_allowed_chars: dict[str, int] = {}
    for char in dataset:
        if char not in my_chars:
            not_allowed_chars[char] = not_allowed_chars.get(char, 0) + 1
    print(f"Number of not allowed characters: {len(not_allowed_chars)}")
    print(f"Not allowed characters: {not_allowed_chars}")
