import re
from pathlib import Path

POLICIES_PATH = Path(__file__).resolve().parents[2] / "data" / "policies"
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "be", "do", "does",
    "i", "you", "we", "my", "your", "it", "to", "of", "for",
    "in", "on", "at", "and", "or", "what", "how", "when",
    "can", "if", "with", "this", "that",
}
SYNONYMS = {
    "e-bike": "electric bike",
    "ebike": "electric bike",
}

def split_policies_into_sections():
    """Splits policies into sections to easily access the data.
    """
    policies_files = sorted(POLICIES_PATH.glob('*.md'))
    policies = []
    for path in policies_files:
        with open(path, "r", encoding="utf-8") as file:
            text = file.read()
            sections = text.split("\n## ")
            for section in sections:
                header, _, content = section.partition("\n")
                header = header.strip()
                content = content.strip()
                if header.startswith("# "):
                    header = header.removeprefix("# ")
                    if not content:
                        continue
                dictionary = {"path": path.name,
                              "header": header,
                              "content": content,
                }
                policies.append(dictionary)
    return policies


def split_text_into_words(text: str) -> set:
    text = text.lower()
    for word, synonym in SYNONYMS.items():
        text = text.replace(word, synonym)
    words = re.findall("[a-z0-9]+", text)
    words = set(words) - STOP_WORDS
    words = {word[:4] for word in words}
    return words


def search_policies(query: str) -> dict:
    """Finds the parts of the documents in data/policies/
    that are relevant to a question.

    Args:
        query: Short english key words, for example "deposit electric bike"

    Returns:
        Dictionary with the query and up to 3 matching sections (file, header, content, score).
        If nothing matches, also an ‘error’ telling to contact the staff.
    """
    query_words = split_text_into_words(query)
    sections = split_policies_into_sections()
    results = []
    for section in sections:
        header_words = split_text_into_words(section["header"])
        content_words = split_text_into_words(section["content"])
        header_hits = len(query_words & header_words)
        content_hits = len(query_words & content_words)
        score = content_hits + 2 * header_hits
        if score > 0:
            dictionary = {"path": section["path"],
                          "header": section["header"],
                          "content": section["content"],
                          "score": score,
            }
            results.append(dictionary)
    top_results = sorted(results, key=lambda result: result["score"], reverse=True)[:3]
    if not top_results:
        response = {"query": query,
                    "results": top_results,
                    "error": "No relevant policy found. Tell the customer to contact the staff.",
        }
    else:
        response = {"query": query,
                    "results": top_results,
        }
    return response