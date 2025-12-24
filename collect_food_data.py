#!/usr/bin/env python3
"""
Activity 01: Data Collection
Collects 200 food products from Open Food Facts API
- 150 with allergens
- 50 without allergens
"""

import requests
import time
import random
import re

BASE_URL = "https://world.openfoodfacts.org"
SEARCH_URL = f"{BASE_URL}/cgi/search.pl"

# Countries to include (USA and UK only)
ALLOWED_COUNTRIES = ["en:united-states", "en:united-kingdom", "en:us", "en:uk"]


def search_products(page=1, page_size=100, with_allergens=True):
    """Search for products with or without allergens"""
    params = {
        "action": "process",
        "tagtype_0": "languages",
        "tag_contains_0": "contains",
        "tag_0": "en",
        "tagtype_1": "states",
        "tag_contains_1": "contains",
        "tag_1": "ingredients-completed",
        "fields": "code,product_name,ingredients_text_en,allergens_tags,url",
        "page_size": page_size,
        "page": page,
        "json": 1,
        "sort_by": "unique_scans_n"
    }

    if with_allergens:
        params["tagtype_2"] = "allergens"
        params["tag_contains_2"] = "contains"
        params["tag_2"] = "en:gluten"  # Start with common allergen

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("products", [])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def search_by_allergen(allergen_tag, page=1, page_size=50):
    """Search for products containing a specific allergen (USA/UK only)"""
    params = {
        "action": "process",
        "tagtype_0": "languages",
        "tag_contains_0": "contains",
        "tag_0": "en",
        "tagtype_1": "allergens",
        "tag_contains_1": "contains",
        "tag_1": allergen_tag,
        "tagtype_2": "countries",
        "tag_contains_2": "contains",
        "tag_2": "en:united-states",  # Primary filter: USA
        "fields": "code,product_name,ingredients_text_en,allergens_tags,countries_tags,url",
        "page_size": page_size,
        "page": page,
        "json": 1,
        "sort_by": "unique_scans_n"
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("products", [])
    except Exception as e:
        print(f"Error fetching allergen {allergen_tag}: {e}")
        return []


def search_without_allergens(page=1, page_size=50, max_retries=3, country="en:united-states"):
    """Search for products without allergens with retry logic (USA/UK only)"""
    params = {
        "action": "process",
        "tagtype_0": "languages",
        "tag_contains_0": "contains",
        "tag_0": "en",
        "tagtype_1": "states",
        "tag_contains_1": "contains",
        "tag_1": "ingredients-completed",
        "tagtype_2": "countries",
        "tag_contains_2": "contains",
        "tag_2": country,
        "fields": "code,product_name,ingredients_text_en,allergens_tags,traces_tags,countries_tags,url",
        "page_size": page_size,
        "page": page,
        "json": 1,
        "sort_by": "unique_scans_n"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(SEARCH_URL, params=params, timeout=60)
            response.raise_for_status()
            return response.json().get("products", [])
        except requests.exceptions.Timeout:
            wait_time = (attempt + 1) * 5
            print(f"  Timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Error fetching products without allergens: {e}")
            return []

    print(f"  Failed after {max_retries} attempts, skipping page {page}")
    return []


def format_allergens(allergens_tags):
    """Format allergens from tags to readable string"""
    if not allergens_tags:
        return ""

    allergens = []
    for tag in allergens_tags:
        # Remove language prefix (e.g., "en:gluten" -> "Gluten")
        if ":" in tag:
            allergen = tag.split(":")[-1]
        else:
            allergen = tag
        allergen = allergen.replace("-", " ").title()
        allergens.append(allergen)

    return ", ".join(allergens)


def clean_text(text):
    """Clean text by removing semicolons, newlines, emojis, and special symbols"""
    if not text:
        return ""
    text = str(text)
    text = text.replace(";", ",")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    # Remove common special symbols
    special_symbols = ["•", "·", "●", "○", "■", "□", "▪", "▫", "►", "◄", "★", "☆",
                       "→", "←", "↑", "↓", "«", "»", "™", "®", "©", "°", "±",
                       "¹", "²", "³", "¼", "½", "¾", "×", "÷", "†", "‡", "§", "¶",
                       "…", "‹", "›", "€", "£", "¥", "¢", "₹", "฿",
                       "_", "*"]  # underscore and asterisk
    for symbol in special_symbols:
        text = text.replace(symbol, " ")

    # Remove emojis and other unicode symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002022"             # bullet point •
        "\U000000B7"             # middle dot ·
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    text = " ".join(text.split())  # Normalize whitespace
    return text


def is_from_allowed_country(product):
    """Check if product is from USA or UK"""
    countries = product.get("countries_tags", [])
    if not countries:
        return False

    for country in countries:
        country_lower = country.lower()
        if any(allowed in country_lower for allowed in ["united-states", "united-kingdom", "us", "uk"]):
            return True
    return False


def is_english_text(text):
    """
    Check if text is primarily in English.
    Returns False if text contains too many non-English characters or patterns.
    """
    if not text or len(text) < 5:
        return False

    text_lower = text.lower()

    # Check for non-ASCII characters (non-English alphabets)
    non_ascii_count = sum(1 for char in text if ord(char) > 127)
    non_ascii_ratio = non_ascii_count / len(text)

    # If more than 10% non-ASCII characters, likely not English
    if non_ascii_ratio > 0.10:
        return False

    # Common non-English patterns to reject
    non_english_patterns = [
        # French
        "é", "è", "ê", "ë", "à", "â", "ô", "î", "ï", "ù", "û", "ç", "œ", "æ",
        # German
        "ä", "ö", "ü", "ß",
        # Spanish/Portuguese
        "ñ", "ã", "õ",
        # Arabic
        "ال", "من", "في",
        # Chinese/Japanese/Korean (check for character ranges)
        # Other indicators
        "ingrédients", "zucker", "azúcar", "açúcar", "zutaten",
        "sucre", "farine", "huile", "lait", "beurre", "œufs",
        "leche", "harina", "aceite", "mantequilla",
        "milch", "mehl", "öl", "butter", "eier",
    ]

    # Count non-English pattern matches
    non_english_matches = sum(1 for pattern in non_english_patterns if pattern in text_lower)

    # If too many non-English patterns found, reject
    if non_english_matches >= 3:
        return False

    # Check for common English food words (positive indicator)
    english_food_words = [
        "sugar", "salt", "water", "oil", "flour", "milk", "cream", "butter",
        "egg", "wheat", "contains", "ingredients", "natural", "flavor",
        "extract", "powder", "syrup", "acid", "vitamin", "protein",
        "modified", "starch", "emulsifier", "preservative", "color",
        "artificial", "organic", "whole", "enriched", "dried"
    ]

    english_matches = sum(1 for word in english_food_words if word in text_lower)

    # Should have at least some English food words
    if english_matches < 2:
        return False

    return True


def is_valid_product(product, require_allergens=True):
    """Check if product has required fields, valid ingredient data, and is in English"""
    code = product.get("code", "")
    name = product.get("product_name", "")
    ingredients = product.get("ingredients_text_en", "")
    allergens = product.get("allergens_tags", [])

    if not code or not name or not ingredients:
        return False

    if len(ingredients) < 10:  # Too short to be useful
        return False

    # Check that product name is in English (no excessive non-ASCII)
    name_non_ascii = sum(1 for char in name if ord(char) > 127)
    if len(name) > 0 and (name_non_ascii / len(name)) > 0.15:
        return False  # Product name has too many non-English characters

    # Check that ingredients are in English
    if not is_english_text(ingredients):
        return False

    # Validate ingredients contain actual food-related content
    # Check for common food words to filter out garbage data
    ingredients_lower = ingredients.lower()
    food_indicators = [
        "sugar", "salt", "water", "oil", "flour", "milk", "cream", "butter",
        "egg", "wheat", "corn", "rice", "starch", "extract", "flavor",
        "acid", "vitamin", "protein", "fat", "sodium", "calcium",
        "natural", "organic", "powder", "syrup", "juice", "puree",
        "vegetable", "fruit", "meat", "fish", "chicken", "beef",
        "tomato", "potato", "onion", "garlic", "spice", "herb"
    ]

    has_food_content = any(word in ingredients_lower for word in food_indicators)
    if not has_food_content:
        return False  # Likely garbage data

    # Check country (must be USA or UK)
    if not is_from_allowed_country(product):
        return False

    if require_allergens:
        return len(allergens) > 0
    else:
        return len(allergens) == 0


def is_truly_allergen_free(product):
    """
    Strict validation to ensure product is 100% allergen-free.
    Checks both allergen tags AND ingredients text for common allergens.
    """
    # Check allergen tags
    allergens = product.get("allergens_tags", [])
    if allergens and len(allergens) > 0:
        return False

    # Check traces tags (may contain)
    traces = product.get("traces_tags", [])
    if traces and len(traces) > 0:
        return False

    # Check ingredients text for common allergen keywords
    ingredients = product.get("ingredients_text_en", "").lower()

    # Common allergen keywords to check in ingredients
    allergen_keywords = [
        # Gluten sources
        "wheat", "barley", "rye", "oat", "spelt", "kamut", "gluten",
        # Dairy
        "milk", "cream", "butter", "cheese", "lactose", "whey", "casein", "dairy",
        # Eggs
        "egg", "albumin", "mayonnaise",
        # Nuts
        "almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia",
        "brazil nut", "chestnut", "nut",
        # Peanuts
        "peanut", "groundnut", "arachis",
        # Soy
        "soy", "soya", "edamame", "tofu", "tempeh",
        # Fish
        "fish", "salmon", "tuna", "cod", "anchovy", "sardine", "mackerel",
        # Shellfish/Crustaceans
        "shrimp", "prawn", "crab", "lobster", "crayfish", "shellfish", "crustacean",
        # Molluscs
        "oyster", "mussel", "clam", "scallop", "squid", "octopus", "mollusc",
        # Sesame
        "sesame", "tahini",
        # Mustard
        "mustard",
        # Celery
        "celery", "celeriac",
        # Lupin
        "lupin", "lupine",
        # Sulphites
        "sulphite", "sulfite", "sulphur dioxide", "sulfur dioxide",
    ]

    for keyword in allergen_keywords:
        if keyword in ingredients:
            return False

    return True


def search_by_allergen_country(allergen_tag, country, page=1, page_size=50):
    """Search for products containing a specific allergen in a specific country"""
    params = {
        "action": "process",
        "tagtype_0": "languages",
        "tag_contains_0": "contains",
        "tag_0": "en",
        "tagtype_1": "allergens",
        "tag_contains_1": "contains",
        "tag_1": allergen_tag,
        "tagtype_2": "countries",
        "tag_contains_2": "contains",
        "tag_2": country,
        "fields": "code,product_name,ingredients_text_en,allergens_tags,countries_tags,url",
        "page_size": page_size,
        "page": page,
        "json": 1,
        "sort_by": "unique_scans_n"
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("products", [])
    except Exception as e:
        print(f"Error fetching allergen {allergen_tag} for {country}: {e}")
        return []


def collect_products_with_allergens(target_count=150):
    """Collect products WITH allergens ensuring diversity (USA & UK only)"""
    collected = {}
    allergen_counts = {}  # Track count per primary allergen

    # Allergen targets for diversity (total = 150)
    allergen_targets = {
        "en:milk": 20,           # Dairy products
        "en:eggs": 18,           # Egg products
        "en:peanuts": 15,        # Peanut products
        "en:nuts": 12,           # Tree nuts
        "en:fish": 12,           # Fish products
        "en:crustaceans": 10,    # Shellfish/crustaceans
        "en:soybeans": 15,       # Soy products
        "en:sesame-seeds": 12,   # Sesame products
        "en:mustard": 8,         # Mustard products
        "en:celery": 8,          # Celery products
        "en:lupin": 5,           # Lupin products
        "en:molluscs": 5,        # Molluscs
        "en:gluten": 10,         # Gluten (wheat) - kept low since it appears with others
    }

    # Countries to search
    countries = ["en:united-states", "en:united-kingdom"]

    print(f"Collecting {target_count} products WITH allergens (USA & UK only)...")
    print("Target distribution:")
    for allergen, target in allergen_targets.items():
        print(f"  {allergen}: {target}")
    print()

    for allergen, target in allergen_targets.items():
        allergen_counts[allergen] = 0

        if len(collected) >= target_count:
            break

        print(f"  Searching for {allergen} (target: {target})...")

        # Search in both USA and UK
        for country in countries:
            if allergen_counts[allergen] >= target or len(collected) >= target_count:
                break

            country_name = "USA" if "united-states" in country else "UK"
            print(f"    Searching in {country_name}...")

            for page in range(1, 6):  # Up to 6 pages per allergen per country
                if allergen_counts[allergen] >= target or len(collected) >= target_count:
                    break

                products = search_by_allergen_country(allergen, country, page=page, page_size=50)

                for product in products:
                    if allergen_counts[allergen] >= target or len(collected) >= target_count:
                        break

                    code = product.get("code", "")
                    allergens_tags = product.get("allergens_tags", [])

                    # Skip if already collected
                    if not code or code in collected:
                        continue

                    # For non-gluten allergens, prefer products where this allergen is primary
                    if allergen != "en:gluten":
                        has_target_allergen = any(allergen in tag or allergen.replace("en:", "") in tag
                                                  for tag in allergens_tags)
                        if not has_target_allergen:
                            continue

                    if is_valid_product(product, require_allergens=True):
                        collected[code] = product
                        allergen_counts[allergen] += 1
                        allergen_name = allergen.replace("en:", "").replace("-", " ").title()
                        print(f"      [{allergen_name}] Found: {allergen_counts[allergen]}/{target} (Total: {len(collected)}/{target_count})")

                time.sleep(0.5)  # Rate limiting

        print(f"  Collected {allergen_counts[allergen]} for {allergen}")

    # Print summary
    print("\nAllergen collection summary:")
    for allergen, count in allergen_counts.items():
        target = allergen_targets.get(allergen, 0)
        status = "✓" if count >= target else "✗"
        print(f"  {status} {allergen}: {count}/{target}")

    return list(collected.values())


def collect_products_without_allergens(target_count=50):
    """Collect products that are 100% allergen-free (USA & UK only)"""
    collected = {}

    # Countries to search
    countries = ["en:united-states", "en:united-kingdom"]

    print(f"\nCollecting {target_count} products WITHOUT any allergens (USA & UK only)...")
    print("Checking: allergen tags, traces tags, AND ingredient keywords\n")

    for country in countries:
        if len(collected) >= target_count:
            break

        country_name = "USA" if "united-states" in country else "UK"
        print(f"  Searching in {country_name}...")

        for page in range(1, 30):  # More pages since strict filtering reduces matches
            if len(collected) >= target_count:
                break

            products = search_without_allergens(page=page, page_size=100, country=country)

            if not products:
                print(f"    No more products found at page {page}")
                break

            for product in products:
                if len(collected) >= target_count:
                    break

                code = product.get("code", "")

                # Skip if already collected or invalid
                if not code or code in collected:
                    continue

                if not is_valid_product(product, require_allergens=False):
                    continue

                # STRICT validation: 100% allergen-free
                if is_truly_allergen_free(product):
                    collected[code] = product
                    name = product.get("product_name", "")[:40]
                    print(f"    Found: {len(collected)}/{target_count} - {name}")

            time.sleep(0.5)

    if len(collected) < target_count:
        print(f"\n  Warning: Only found {len(collected)} truly allergen-free products")

    return list(collected.values())


def save_to_file(products, filename="foodraw.txt"):
    """Save products to semicolon-separated file"""
    with open(filename, "w", encoding="utf-8") as f:
        for idx, product in enumerate(products, 1):
            code = product.get("code", "")
            name = clean_text(product.get("product_name", ""))
            ingredients = clean_text(product.get("ingredients_text_en", ""))
            allergens = format_allergens(product.get("allergens_tags", []))

            # Build the URL
            url = f"https://world.openfoodfacts.org/product/{code}"

            # Format: id;name;ingredients;allergens;link
            line = f"{idx};{name};{ingredients};{allergens};{url}\n"
            f.write(line)

    print(f"\nSaved {len(products)} products to {filename}")


def main():
    print("=" * 60)
    print("Open Food Facts Data Collection")
    print("=" * 60)

    # Collect products with allergens (150)
    products_with_allergens = collect_products_with_allergens(150)
    print(f"\nCollected {len(products_with_allergens)} products with allergens")

    # Collect products without allergens (50)
    products_without_allergens = collect_products_without_allergens(50)
    print(f"Collected {len(products_without_allergens)} products without allergens")

    # Combine all products
    all_products = products_with_allergens + products_without_allergens

    # Shuffle to mix them up
    random.shuffle(all_products)

    print(f"\nTotal products: {len(all_products)}")

    # Save to file
    save_to_file(all_products, "foodraw.txt")

    # Print summary
    with_allergens = sum(1 for p in all_products if p.get("allergens_tags"))
    without_allergens = len(all_products) - with_allergens

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Products with allergens: {with_allergens}")
    print(f"  Products without allergens: {without_allergens}")
    print(f"  Total: {len(all_products)}")
    print("=" * 60)


if __name__ == "__main__":
    main()