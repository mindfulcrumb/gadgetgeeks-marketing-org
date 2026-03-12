#!/usr/bin/env python3
"""
Copy Audit — Automated 25-check scanner for the blog pipeline.

Extracts blog HTML from blog-pipeline.json, runs the full Copy Police
scanner against it, and updates the pipeline with results.

This runs in GitHub Actions AFTER the blog writer agent and BEFORE
the publisher agent. Blogs that fail get status "qa_blocked".
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent.parent
PIPELINE_PATH = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"
COPY_RULES_PATH = REPO_ROOT / "config" / "copy-rules.json"
INVENTORY_PATH = REPO_ROOT / "config" / "store-inventory.json"


def load_rules() -> dict:
    """Load the copy rules JSON."""
    if COPY_RULES_PATH.exists():
        return json.loads(COPY_RULES_PATH.read_text(encoding="utf-8"))
    return {"banned_words": [], "banned_phrases": []}


def scan_blog_html(html: str, rules: dict) -> dict:
    """Run the 25-check scanner against blog HTML content.

    Returns a dict with rating, violations, warnings, and feedback.
    """
    # Strip HTML to get plain text
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    text_lower = text.lower()
    violations = []
    warnings = []
    feedback = []
    critical_count = 0

    # ===== CHECK 1: BANNED WORDS =====
    # Words only banned in metaphorical/marketing usage, not literal tech context
    context_sensitive = {"unlock", "unlocking", "navigate", "navigating", "journey", "landscape"}
    literal_contexts = ["activation lock", "activation unlock", "unlock it", "unlock activation",
                        "phone unlock", "carrier unlock", "unlock the phone", "unlock the device",
                        "navigate to", "navigating to", "unlock for me",
                        "can't unlock", "won't unlock", "bypass activation"]

    banned_words = rules.get("banned_words", [])
    for word in set(banned_words):
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = list(re.finditer(pattern, text_lower))
        for m in matches:
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            context = text[start:end].strip()
            context_lower = context.lower()

            # Skip context-sensitive words when used literally (not as marketing fluff)
            if word in context_sensitive:
                if any(lc in context_lower for lc in literal_contexts):
                    continue

            feedback.append({
                "check_id": 1, "check_name": "Banned Words", "severity": "critical",
                "location": f"...{context}...",
                "issue": f'Banned word "{word}" found',
                "fix": f'Replace "{word}" with a plain, specific alternative'
            })
            critical_count += 1

    # ===== CHECK 2: BANNED PHRASES =====
    banned_phrases = rules.get("banned_phrases", [])
    for phrase in banned_phrases:
        if phrase in text_lower:
            idx = text_lower.index(phrase)
            start = max(0, idx - 20)
            end = min(len(text), idx + len(phrase) + 20)
            context = text[start:end].strip()
            feedback.append({
                "check_id": 2, "check_name": "Banned Phrases", "severity": "critical",
                "location": f"...{context}...",
                "issue": f'Banned phrase "{phrase}" found',
                "fix": "Cut the phrase entirely or rewrite the sentence"
            })
            critical_count += 1

    # ===== CHECK 3: NEGATION DANCE =====
    not_its = re.findall(
        r"(?:It'?s not|This (?:is)?n'?t|Not a |Not just a )[^.!?]{3,60}[.!?]\s*(?:It'?s |This is |It is )[^.!?]{3,60}[.!?]",
        text, re.IGNORECASE
    )
    for nip in not_its:
        feedback.append({
            "check_id": 3, "check_name": "Negation Dance", "severity": "critical",
            "location": nip[:80],
            "issue": "'It's not X. It's Y.' reframe pattern — textbook AI",
            "fix": "State what it IS directly. Cut the 'not' setup."
        })
        critical_count += 1

    # ===== CHECK 4: TRIPLE PARALLEL =====
    triple_patterns = re.findall(
        r'(?:No |Every |Not |More |Less |Better |Without |Stop |Start |Same )'
        r'[^.!,;]{3,30}[.,;!]\s*'
        r'(?:No |Every |Not |More |Less |Better |Without |Stop |Start |Same )'
        r'[^.!,;]{3,30}[.,;!]\s*'
        r'(?:No |Every |Not |More |Less |Better |Without |Stop |Start |Same )'
        r'[^.!,;]{3,30}[.,;!]',
        text
    )
    for tp in triple_patterns:
        feedback.append({
            "check_id": 4, "check_name": "Triple Parallel", "severity": "critical",
            "location": tp[:80],
            "issue": "Three parallel sentences with same starter pattern",
            "fix": "Break one pattern or reduce to two"
        })
        critical_count += 1

    # ===== CHECK 5: DEFINITION OPENER =====
    first_chunk = text[:500].lower()
    def_starters = [
        r'^[a-z][\w\s]+ is the (?:art|practice|process|act|science) of',
        r'^[a-z][\w\s]+ refers to',
        r'^when it comes to',
        r'^in the (?:world|realm|landscape) of',
    ]
    for ds in def_starters:
        if re.search(ds, first_chunk):
            feedback.append({
                "check_id": 5, "check_name": "Definition Opener", "severity": "critical",
                "location": text[:100],
                "issue": "Opens by defining the topic — AI tell #1",
                "fix": "Start with a scenario, bold claim, specific fact, or question"
            })
            critical_count += 1

    # ===== CHECK 6: UNIFORM BULLET LENGTH =====
    bullet_groups = re.findall(r'<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>', html, re.DOTALL)
    for bg in bullet_groups:
        items = re.findall(r'<li[^>]*>(.*?)</li>', bg, re.DOTALL)
        if len(items) >= 3:
            clean_items = [re.sub(r'<[^>]+>', '', item).strip() for item in items]
            word_counts = [len(item.split()) for item in clean_items if item]
            if word_counts and len(word_counts) >= 3:
                avg_wc = sum(word_counts) / len(word_counts)
                wc_var = sum((w - avg_wc) ** 2 for w in word_counts) / len(word_counts)
                if wc_var < 4.0 and avg_wc > 3:
                    feedback.append({
                        "check_id": 6, "check_name": "Uniform Bullets", "severity": "warning",
                        "location": f"{len(word_counts)} items, ~{avg_wc:.0f} words each",
                        "issue": f"Bullet items too uniform (variance {wc_var:.1f})",
                        "fix": "Vary bullet length — mix fragments with longer explanations"
                    })
                    warnings.append("UNIFORM BULLETS")

    # ===== CHECK 7: TRANSITION STARTERS =====
    lines = html.split('\n')
    transition_words = [
        "firstly", "secondly", "thirdly", "furthermore", "moreover",
        "additionally", "in addition", "finally", "in summary",
        "consequently", "thus", "hence", "therefore", "first,", "second,", "third,",
    ]
    for line_num, line in enumerate(lines, 1):
        stripped = re.sub(r'<[^>]+>', '', line).strip().lower()
        for tw in transition_words:
            if stripped.startswith(tw):
                feedback.append({
                    "check_id": 7, "check_name": "Transition Starter", "severity": "critical",
                    "location": f"Line {line_num}: {stripped[:60]}",
                    "issue": f'Starts with "{tw}" — AI tell',
                    "fix": "Cut the transition word. Start with substance."
                })
                critical_count += 1

    # ===== CHECK 8: SUMMARY ENDING =====
    last_500 = text[-500:].lower()
    summary_signals = ["in summary", "to summarize", "in conclusion", "to recap",
                       "as we've seen", "we've explored", "we've covered", "all in all", "to sum up"]
    for ss in summary_signals:
        if ss in last_500:
            feedback.append({
                "check_id": 8, "check_name": "Summary Ending", "severity": "critical",
                "location": f"Last 500 chars contain '{ss}'",
                "issue": "Ends by summarizing/recapping — AI tell",
                "fix": "Just stop. Or end with a forward-looking statement or CTA."
            })
            critical_count += 1

    # ===== CHECK 9: HEDGING =====
    hedge_patterns = [
        "some might argue", "on the other hand", "while it's true",
        "could potentially", "may potentially", "might consider",
        "results may vary", "in some cases", "under certain circumstances",
    ]
    for hedge in hedge_patterns:
        if hedge in text_lower:
            feedback.append({
                "check_id": 9, "check_name": "Hedging", "severity": "critical",
                "location": hedge,
                "issue": f'Hedging: "{hedge}"',
                "fix": "Have an opinion. State it directly."
            })
            critical_count += 1

    # ===== CHECK 10: VAGUE SUPERLATIVES =====
    vague = re.findall(
        r'\b(?:significant|remarkable|incredible|amazing|outstanding|exceptional|unmatched|superior|world-class|best-in-class|industry-leading|state-of-the-art|premium quality|high quality|top quality)\b',
        text_lower
    )
    if len(vague) >= 2:
        feedback.append({
            "check_id": 10, "check_name": "Vague Superlatives", "severity": "warning",
            "location": str(vague[:5]),
            "issue": f"{len(vague)} vague superlatives without proof",
            "fix": "Replace each with a specific number, testimonial, or named source"
        })
        warnings.append("VAGUE SUPERLATIVES")

    # ===== CHECK 11: UNIFORM PARAGRAPH LENGTH =====
    paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    clean_paras = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if len(re.sub(r'<[^>]+>', '', p).strip()) > 20]
    if len(clean_paras) >= 4:
        para_wc = [len(p.split()) for p in clean_paras]
        avg_pwc = sum(para_wc) / len(para_wc)
        pwc_var = sum((w - avg_pwc) ** 2 for w in para_wc) / len(para_wc)
        pwc_std = pwc_var ** 0.5
        single_line = sum(1 for wc in para_wc if wc <= 8)
        if pwc_std < 5.0 and single_line == 0:
            feedback.append({
                "check_id": 11, "check_name": "Uniform Paragraphs", "severity": "warning",
                "location": f"std dev {pwc_std:.1f}, {single_line} single-line paragraphs",
                "issue": "Paragraph lengths too uniform, no single-line paragraphs",
                "fix": "Force one 1-sentence paragraph per section"
            })
            warnings.append("UNIFORM PARAGRAPHS")

    # ===== CHECK 12: SENTENCE LENGTH VARIATION (MOST IMPORTANT) =====
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if len(sentences) >= 6:
        lengths = [len(s.split()) for s in sentences]
        short_count = sum(1 for l in lengths if l <= 5)
        long_count = sum(1 for l in lengths if l >= 20)
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        if short_count < 2:
            feedback.append({
                "check_id": 12, "check_name": "Sentence Length - Short", "severity": "critical",
                "location": f"Only {short_count} sentences under 6 words",
                "issue": "Not enough short punchy sentences — AI detection flag #1",
                "fix": "Add fragments: 'Game over.' 'Worth it.' 'That changed everything.'"
            })
            critical_count += 1

        if long_count == 0:
            feedback.append({
                "check_id": 12, "check_name": "Sentence Length - Long", "severity": "warning",
                "location": "0 sentences over 20 words",
                "issue": "No flowing long sentences",
                "fix": "Add one 25+ word conversational sentence"
            })
            warnings.append("NO LONG SENTENCES")

        if std_dev < 5.0:
            feedback.append({
                "check_id": 12, "check_name": "Sentence Length - Variance", "severity": "critical",
                "location": f"std dev = {std_dev:.1f} (need 5+)",
                "issue": "#1 AI detector signal — sentences too uniform",
                "fix": "Mix 3-word punches with 25-word flows"
            })
            critical_count += 1

    # ===== CHECK 13: STRATEGIC IMPERFECTION =====
    fragment_count = sum(1 for s in sentences if len(s.split()) <= 4) if sentences else 0
    has_em_dash = bool(re.search(r'[\u2014]|&mdash;|—', html))
    casual_markers = sum(1 for m in ["yeah", "nope", "kinda", "honestly", "look,", "listen,", "damn", "hell"]
                         if m in text_lower)
    imperfection_score = fragment_count + (1 if has_em_dash else 0) + casual_markers
    if imperfection_score < 2 and len(sentences) > 10:
        feedback.append({
            "check_id": 13, "check_name": "Strategic Imperfection", "severity": "critical",
            "location": f"Score: {imperfection_score} (need 2+)",
            "issue": "Too grammatically perfect — no fragments, no em-dashes, no casual language",
            "fix": "Add fragments, em-dashes, or casual asides. Too polished = AI."
        })
        critical_count += 1

    # ===== CHECK 14: RHETORICAL QUESTIONS =====
    all_qs = re.findall(r'[^<>]{10,60}\?', text)
    if len(all_qs) < 2 and len(text) > 1000:
        feedback.append({
            "check_id": 14, "check_name": "Rhetorical Questions", "severity": "warning",
            "location": f"Only {len(all_qs)} questions found",
            "issue": "Too few rhetorical questions",
            "fix": "Add 2-3 questions that create internal dialogue"
        })
        warnings.append("FEW RHETORICAL QUESTIONS")

    # ===== CHECK 15: CONTRACTIONS =====
    contractions = ["don't", "won't", "can't", "isn't", "wasn't", "aren't",
                    "didn't", "couldn't", "shouldn't", "wouldn't", "haven't",
                    "hasn't", "we're", "they're", "you're", "it's", "that's",
                    "there's", "here's", "what's", "let's", "we've", "you've", "they've"]
    contraction_count = sum(text_lower.count(c) for c in contractions)
    # Count formal alternatives
    formal_alternatives = ["do not", "will not", "can not", "cannot", "is not", "was not",
                           "are not", "did not", "could not", "should not", "would not",
                           "have not", "has not", "we are", "they are", "you are",
                           "it is", "that is", "there is", "what is", "let us"]
    formal_count = sum(text_lower.count(f) for f in formal_alternatives)
    total_opportunities = contraction_count + formal_count
    contraction_rate = (contraction_count / total_opportunities * 100) if total_opportunities > 0 else 0

    if contraction_rate < 70:
        feedback.append({
            "check_id": 15, "check_name": "Contractions", "severity": "critical",
            "location": f"Rate: {contraction_rate:.0f}% (need 75%+)",
            "issue": f"Contraction rate too low — {formal_count} missed contractions",
            "fix": "Convert all 'do not'→'don't', 'it is'→'it's', etc."
        })
        critical_count += 1

    # ===== CHECK 16: FEATURES WITHOUT BENEFITS =====
    feature_lists = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL)
    pure_features = 0
    for feat in feature_lists:
        clean = re.sub(r'<[^>]+>', '', feat).strip()
        if re.match(r'^[\d]+[gx%]?\s', clean) or re.match(r'^[A-Z][a-z]+[-\s]', clean):
            if not re.search(r'(?:so you|which means|giving you|meaning|because|that.s why)', clean.lower()):
                pure_features += 1
    if pure_features >= 4:
        feedback.append({
            "check_id": 16, "check_name": "Features Without Benefits", "severity": "warning",
            "location": f"{pure_features} pure feature items",
            "issue": "List items are features without benefit chains",
            "fix": "Add 'so you...' or 'which means...' after each feature"
        })
        warnings.append("FEATURES WITHOUT BENEFITS")

    # ===== CHECK 22: ACTIVE VOICE =====
    passive = re.findall(r'\b(?:is|are|was|were|been|being)\s+(?:\w+ed|made|done|given|taken|found|seen|known)\b', text_lower)
    if len(passive) >= 3:
        feedback.append({
            "check_id": 22, "check_name": "Active Voice", "severity": "warning",
            "location": f"{len(passive)} passive constructions",
            "issue": "Too many passive voice constructions",
            "fix": "Rewrite in active voice throughout"
        })
        warnings.append("PASSIVE VOICE")

    # ===== CHECK 23: LAZY PATTERNS =====
    your_pattern = re.findall(r'Your \w+[.,]', text)
    if len(your_pattern) >= 5:
        feedback.append({
            "check_id": 23, "check_name": "Lazy Patterns - Possessive", "severity": "warning",
            "location": f"{len(your_pattern)}x 'Your X.' pattern",
            "issue": "Too many 'Your X.' sentence starters",
            "fix": "Vary openings"
        })
        warnings.append("POSSESSIVE PATTERN")

    excl_count = text.count('!')
    if excl_count > 3:
        feedback.append({
            "check_id": 23, "check_name": "Lazy Patterns - Exclamation", "severity": "warning",
            "location": f"{excl_count} exclamation marks",
            "issue": "Too many exclamation marks (max 2)",
            "fix": "Cut exclamation marks — let the words do the work"
        })
        warnings.append("EXCLAMATION OVERUSE")

    # ===== CHECK 24: PERIOD-CONJUNCTION =====
    period_conj = re.findall(r'[a-z\d"][.!]\s+(?:And |But |Or )[a-z]', text, re.IGNORECASE)
    for pcm in period_conj:
        feedback.append({
            "check_id": 24, "check_name": "Period-Conjunction", "severity": "critical",
            "location": pcm,
            "issue": "'Sentence. And/But continuation' — AI fragmenting",
            "fix": "Use a comma: 'sentence, and continuation'"
        })
        critical_count += 1

    # ===== CHECK 25: STACCATO FRAGMENTS =====
    staccato = re.findall(r'(?:[A-Z][^.!?]{1,25}[.!?]\s*){3,}', text)
    for sr in staccato:
        frags = [f.strip() for f in re.split(r'[.!?]+', sr) if f.strip()]
        short_frags = [f for f in frags if len(f.split()) <= 5]
        if len(short_frags) >= 3 and len(frags) >= 3:
            sample = '. '.join(short_frags[:3])
            feedback.append({
                "check_id": 25, "check_name": "Staccato Fragments", "severity": "critical",
                "location": sample[:80],
                "issue": "3+ consecutive short fragments — AI chops thoughts",
                "fix": "Connect with commas in flowing sentences"
            })
            critical_count += 1

    # ===== CHECK 26: LINK VALIDATION =====
    inventory = {}
    if INVENTORY_PATH.exists():
        inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    if inventory:
        valid_products = set(inventory.get("products", {}).keys())
        valid_collections = set(inventory.get("collections", {}).keys())
        valid_pages = set(inventory.get("pages", {}).keys())
        aliases = inventory.get("handle_aliases", {})

        hrefs = re.findall(r'href="(/[^"]+)"', html)
        for href in hrefs:
            parts = href.strip("/").split("/")
            if len(parts) != 2:
                continue
            resource_type, handle = parts[0], parts[1]

            if resource_type == "products" and handle not in valid_products:
                real = aliases.get(handle, None)
                fix_msg = f'Use "/products/{real}" instead' if real else "Check store-inventory.json for valid handles"
                feedback.append({
                    "check_id": 26, "check_name": "Broken Link", "severity": "critical",
                    "location": href,
                    "issue": f'Product handle "{handle}" does not exist in store',
                    "fix": fix_msg
                })
                critical_count += 1
            elif resource_type == "collections" and handle not in valid_collections:
                real = aliases.get(handle, "").replace("collection:", "") if aliases.get(handle, "").startswith("collection:") else None
                fix_msg = f'Use "/collections/{real}" instead' if real else "Check store-inventory.json for valid collections"
                feedback.append({
                    "check_id": 26, "check_name": "Broken Link", "severity": "critical",
                    "location": href,
                    "issue": f'Collection handle "{handle}" does not exist in store',
                    "fix": fix_msg
                })
                critical_count += 1
            elif resource_type == "pages" and handle not in valid_pages:
                real = aliases.get(handle, "").replace("page:", "") if aliases.get(handle, "").startswith("page:") else None
                fix_msg = f'Use "/pages/{real}" instead' if real else "Check store-inventory.json for valid pages"
                feedback.append({
                    "check_id": 26, "check_name": "Broken Link", "severity": "critical",
                    "location": href,
                    "issue": f'Page handle "{handle}" does not exist in store',
                    "fix": fix_msg
                })
                critical_count += 1

    # ===== CHECK 27: TRIPLE LIST PATTERN (Chad Rule C2) =====
    list_groups = re.findall(r'<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>', html, re.DOTALL)
    list_item_counts = []
    for lg in list_groups:
        items = re.findall(r'<li[^>]*>', lg)
        if len(items) >= 2:
            list_item_counts.append(len(items))
    if list_item_counts:
        triple_lists = sum(1 for c in list_item_counts if c == 3)
        if len(list_item_counts) > 0 and triple_lists / len(list_item_counts) >= 0.5:
            feedback.append({
                "check_id": 27, "check_name": "Triple List Pattern", "severity": "critical",
                "location": f"{triple_lists}/{len(list_item_counts)} lists have exactly 3 items",
                "issue": "AI defaults to 3-item lists. Real writers vary: 2, 4, 5, 7 items.",
                "fix": "Add a 4th item or cut to 2. Never default to 3."
            })
            critical_count += 1

    # Also check inline triple patterns: "X, Y, and Z" appearing 3+ times
    inline_triples = re.findall(
        r'\b\w+(?:,\s+\w+){1}\s*,?\s*and\s+\w+\b', text
    )
    if len(inline_triples) >= 4:
        feedback.append({
            "check_id": 27, "check_name": "Inline Triple Pattern", "severity": "warning",
            "location": f"{len(inline_triples)} inline 'X, Y, and Z' patterns",
            "issue": "Too many three-item inline lists — AI fingerprint",
            "fix": "Vary: use 2-item pairs or 4+ item lists"
        })
        warnings.append("INLINE TRIPLES")

    # ===== CHECK 28: EM DASH DENSITY (Chad Rule C3) =====
    em_dash_count = len(re.findall(r'[\u2014]|&mdash;|—', html))
    word_count_total = len(text.split())
    if word_count_total > 0:
        em_per_1000 = (em_dash_count / word_count_total) * 1000
        max_em = rules.get("em_dash_max_per_1000", 3)
        if em_per_1000 > 5:
            feedback.append({
                "check_id": 28, "check_name": "Em Dash Density", "severity": "critical",
                "location": f"{em_dash_count} em dashes in {word_count_total} words ({em_per_1000:.1f}/1000)",
                "issue": f"Em dash overuse — {em_per_1000:.1f} per 1,000 words (max {max_em}). Chad's #1 AI fingerprint.",
                "fix": f"Cut to max {max_em} per 1,000 words. Convert extras to commas, periods, or parentheses."
            })
            critical_count += 1
        elif em_per_1000 > max_em:
            feedback.append({
                "check_id": 28, "check_name": "Em Dash Density", "severity": "warning",
                "location": f"{em_dash_count} em dashes in {word_count_total} words ({em_per_1000:.1f}/1000)",
                "issue": f"Em dash density {em_per_1000:.1f}/1000 exceeds limit of {max_em}/1000",
                "fix": "Replace some em dashes with commas or periods."
            })
            warnings.append("EM DASH DENSITY")

    # ===== CHECK 29: PRODUCT MENTION DENSITY (Chad Rule C4 — Sell Test) =====
    # Split HTML by H2 sections and check each for selling language
    h2_sections = re.split(r'<h2[^>]*>', html)
    sell_phrases = [
        "65-point inspection", "90-day warranty", "30-day return", "free shipping",
        "gadget geeks", "gadgetgeeks", "check availability", "shop now",
        "check price", "find yours", "see the savings",
    ]
    sell_phrase_pattern = '|'.join(re.escape(sp) for sp in sell_phrases)
    product_callout_pattern = r'blog-product-callout|blog-product-cta|/products/|/collections/'

    sections_with_sell = 0
    total_content_sections = 0
    for section in h2_sections[1:]:  # Skip intro before first H2
        section_lower = section.lower()
        section_text = re.sub(r'<[^>]+>', ' ', section).strip()
        if len(section_text.split()) < 30:  # Skip tiny sections
            continue
        total_content_sections += 1
        has_sell = bool(re.search(sell_phrase_pattern, section_lower)) or \
                   bool(re.search(product_callout_pattern, section_lower))
        if has_sell:
            sections_with_sell += 1

    if total_content_sections >= 3 and sections_with_sell == total_content_sections:
        feedback.append({
            "check_id": 29, "check_name": "Product Mention Density", "severity": "critical",
            "location": f"ALL {total_content_sections} sections contain selling language",
            "issue": "Every section sells — this reads as an ad pretending to be a blog",
            "fix": "At least one section (150+ words) must be pure information: no products, no CTAs, no brand mentions."
        })
        critical_count += 1

    # ===== CHECK 30: DEPTH MARKERS (Chad Rule C1 — Original Insight) =====
    depth_markers_list = rules.get("depth_markers", [
        "i tested", "we found", "our data shows", "in our experience",
        "we've seen", "our return rate", "our inspection",
        "despite what", "i disagree", "unpopular opinion", "hot take",
        "here's what actually", "what most sites won't tell",
        "from our catalog", "in our warehouse", "when we open",
    ])
    depth_found = sum(1 for dm in depth_markers_list if dm in text_lower)
    if depth_found == 0:
        feedback.append({
            "check_id": 30, "check_name": "Depth Markers", "severity": "warning",
            "location": "No original insight markers found in entire post",
            "issue": "Zero signals of proprietary data, real experience, or contrarian takes",
            "fix": "Add at least one: proprietary data, customer story, insider detail, or debatable opinion"
        })
        warnings.append("NO DEPTH MARKERS")

    # ===== CHECK 31: LIST LENGTH UNIFORMITY (Chad Rule C7) =====
    if len(list_item_counts) >= 2:
        unique_counts = set(list_item_counts)
        if len(unique_counts) == 1:
            feedback.append({
                "check_id": 31, "check_name": "List Length Uniformity", "severity": "warning",
                "location": f"All {len(list_item_counts)} lists have exactly {list_item_counts[0]} items",
                "issue": "Every list has the same item count — AI pattern",
                "fix": "Vary list lengths across the post: mix 2, 4, 5, 7 items"
            })
            warnings.append("UNIFORM LIST LENGTHS")

    # ===== MARKETING CLICHÉS =====
    cliches = [
        "peace of mind", "one-stop shop", "takes the guesswork out",
        "makes all the difference", "the bottom line", "without breaking the bank",
        "selling peace of mind", "your one-stop", "at the end of the day",
    ]
    for cliche in cliches:
        if cliche in text_lower:
            feedback.append({
                "check_id": 99, "check_name": "Marketing Cliché", "severity": "warning",
                "location": cliche,
                "issue": f'Marketing cliché: "{cliche}" — no human says this',
                "fix": "Cut it. Say what you actually mean in plain language."
            })
            warnings.append(f"CLICHE: {cliche}")

    # ===== RATING =====
    warning_count = len(warnings)
    if critical_count == 0 and warning_count <= 1:
        rating = "EXCELLENT"
    elif critical_count == 0 and warning_count <= 3:
        rating = "GOOD"
    elif critical_count <= 2:
        rating = "NEEDS_WORK"
    else:
        rating = "BLOCKED"

    # Determine status
    if rating in ("EXCELLENT", "GOOD"):
        status = "qa_approved"
    elif rating == "NEEDS_WORK":
        status = "qa_rejected"
    else:
        status = "qa_blocked"

    return {
        "rating": rating,
        "status": status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "feedback": feedback,
        "metrics": {
            "word_count": len(text.split()),
            "sentence_count": len(sentences) if sentences else 0,
            "rhythm_sd": round(std_dev, 1) if sentences and len(sentences) >= 6 else 0,
            "contraction_rate": round(contraction_rate),
            "passive_count": len(passive),
            "short_sentences": short_count if sentences and len(sentences) >= 6 else 0,
            "long_sentences": long_count if sentences and len(sentences) >= 6 else 0,
            "imperfection_score": imperfection_score,
        }
    }


def audit_pipeline():
    """Scan all draft_ready blogs in the pipeline."""
    if not PIPELINE_PATH.exists():
        print("No blog-pipeline.json found. Nothing to audit.")
        return 0

    pipeline = json.loads(PIPELINE_PATH.read_text(encoding="utf-8"))
    rules = load_rules()
    audited = 0
    blocked = 0

    for blog in pipeline.get("blogs", []):
        if blog.get("status") != "draft_ready":
            continue

        title = blog.get("title", "Untitled")
        content = blog.get("content", "")
        if not content or len(content) < 200:
            print(f"  SKIP: {title} — content too short")
            continue

        print(f"\n{'='*70}")
        print(f"  AUDITING: {title}")
        print(f"{'='*70}")

        result = scan_blog_html(content, rules)

        # Update the blog entry
        blog["status"] = result["status"]
        blog["qa_score"] = {
            "rating": result["rating"],
            "total_flags": result["critical_count"] + result["warning_count"],
            "critical_violations": result["critical_count"],
            "warnings": result["warning_count"],
            "rhythm_sd": result["metrics"]["rhythm_sd"],
            "contraction_rate": result["metrics"]["contraction_rate"],
            "passive_count": result["metrics"]["passive_count"],
            "word_count": result["metrics"]["word_count"],
        }
        blog["qa_feedback"] = result["feedback"]
        blog["qa_reviewed_at"] = datetime.now(timezone.utc).isoformat()
        blog["qa_reviewed_by"] = "QUILL (copy_audit.py)"

        # Print results
        print(f"  Rating: {result['rating']}")
        print(f"  Status: {result['status']}")
        print(f"  Critical: {result['critical_count']} | Warnings: {result['warning_count']}")
        print(f"  Word count: {result['metrics']['word_count']}")
        print(f"  Rhythm SD: {result['metrics']['rhythm_sd']}")
        print(f"  Contraction rate: {result['metrics']['contraction_rate']}%")

        if result["feedback"]:
            print(f"\n  FEEDBACK ({len(result['feedback'])} items):")
            print(f"  {'-'*50}")
            for i, fb in enumerate(result["feedback"], 1):
                severity = "CRITICAL" if fb["severity"] == "critical" else "WARNING"
                print(f"  {i}. [{severity}] Check {fb['check_id']}: {fb['check_name']}")
                print(f"     Issue: {fb['issue']}")
                print(f"     Location: {fb['location'][:80]}")
                print(f"     Fix: {fb['fix']}")

        if result["rating"] in ("NEEDS_WORK", "BLOCKED"):
            blocked += 1
            print(f"\n  VERDICT: DOES NOT SHIP. {result['critical_count']} critical violations.")
        else:
            print(f"\n  VERDICT: {result['rating']}. Copy can ship.")

        print(f"{'='*70}")
        audited += 1

    # Save updated pipeline
    pipeline_path = PIPELINE_PATH
    pipeline_path.write_text(json.dumps(pipeline, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nAudited {audited} blog(s). {blocked} blocked.")
    return blocked


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        # Scan a single HTML file
        filepath = sys.argv[2] if len(sys.argv) > 2 else ""
        if not filepath or not Path(filepath).exists():
            print("Usage: python copy_audit.py scan <file.html>")
            sys.exit(1)
        html = Path(filepath).read_text(encoding="utf-8")
        rules = load_rules()
        result = scan_blog_html(html, rules)
        print(json.dumps(result, indent=2))
    else:
        # Audit the pipeline
        blocked = audit_pipeline()
        sys.exit(1 if blocked > 0 else 0)
