# Food Allergen Dataset Preparation

This project collects, cleanses, and maps food product data with allergen information from the Open Food Facts API.

## Requirements

- Python 3.8+
- Required packages:
  ```
  pip install requests openpyxl
  ```

## Project Structure

```
Dataset Preparation Python/
├── collect_food_data.py      # Activity 01: Data Collection
├── cleanse_data.py           # Activity 02: Data Cleansing
├── map_allergens.py          # Activity 03: Data Mapping
├── foodraw.txt               # Output: Raw collected data
├── foodraw.xlsx              # Output: Cleansed Excel file
├── foodpreprocessed.xlsx     # Output: Final mapped file (for app)
└── README.md                 # This file
```

## How to Run

### Step 1: Install Dependencies

```bash
pip install requests openpyxl
```

### Step 2: Run Scripts in Order

Run each script one by one in this exact order:

```bash
python collect_food_data.py
python cleanse_data.py
python map_allergens.py
```

**Note:** Step 1 takes the longest (5-10 minutes) as it fetches data from the API.

---

## Activity Details

### Activity 01: Data Collection (`collect_food_data.py`)

**Purpose:** Collects 200 food products from Open Food Facts API

**Output:** `foodraw.txt`

**Requirements Met:**
- 150 products WITH allergens (diverse distribution)
- 50 products WITHOUT any allergens (100% allergen-free)
- **Products from USA and UK only**
- **Product name and ingredients in English only**
- Data saved as semicolon-separated `.txt` file
- Each product tagged with unique ID
- Validates ingredients contain actual food content (filters garbage data)

**Data Format:**
```
id;name;ingredients;allergens;link
1;Product Name;ingredient list...;Milk, Eggs;https://...
2;Another Product;ingredients...;;https://...  (no allergens)
```

---

### Activity 02: Data Cleansing (`cleanse_data.py`)

**Purpose:** Export and cleanse data using Excel formulas

**Input:** `foodraw.txt`

**Output:** `foodraw.xlsx`

**Requirements Met:**
- Exports data to Excel file
- Columns: id, name, link, ingredients_raw, allergens_raw, ingredients, allergensraw
- Uses **Excel formulas** to clean ingredients and allergens:
  - Converts to lowercase
  - Removes numbers and special characters
  - Keeps only alphabets, spaces, and commas

**Excel Column Structure:**

| Column | Header | Description | Color |
|--------|--------|-------------|-------|
| A | id | Product ID | Blue |
| B | name | Product name | Blue |
| C | link | Product URL | Blue |
| D | ingredients_raw | Original ingredients | Orange |
| E | allergens_raw | Original allergens | Orange |
| F | ingredients | Cleaned (Excel formula) | Green |
| G | allergensraw | Cleaned (Excel formula) | Green |

---

### Activity 03: Data Mapping (`map_allergens.py`)

**Purpose:** Map allergens to the 9 common allergens using AI-generated mappings

**Input:** `foodraw.xlsx`

**Output:** `foodpreprocessed.xlsx` (This file is used by the mobile app)

**Requirements Met:**
- Adds `allergensmapped` column
- Data in lowercase
- Maps to 9 common allergens:

| # | Allergen | Example Keywords |
|---|----------|------------------|
| 1 | milk | milk, dairy, lactose, casein, whey, butter, cream |
| 2 | egg | egg, albumin, mayonnaise, meringue |
| 3 | peanut | peanut, groundnut, arachis |
| 4 | tree nut | almond, cashew, walnut, hazelnut, pistachio |
| 5 | wheat | wheat, gluten, flour, bread, semolina |
| 6 | soy | soy, soya, tofu, tempeh, miso |
| 7 | fish | fish, salmon, tuna, cod, anchovy |
| 8 | shellfish | shrimp, crab, lobster, mussel, oyster, squid |
| 9 | sesame | sesame, tahini, hummus |

**Final Output Columns:**

| Column | Header |
|--------|--------|
| A | id |
| B | name |
| C | link |
| D | ingredients |
| E | allergensraw |
| F | allergensmapped |

---

## Troubleshooting

### Timeout Errors (Step 1)
If you get timeout errors during data collection, the script will automatically retry up to 3 times with increasing wait times.

### Circular Reference Warning (Step 3)
If you see this warning in Excel, rerun:
```bash
python cleanse_data.py
python map_allergens.py
```

### Missing Data
If `foodraw.txt` has fewer than 200 products, rerun:
```bash
python collect_food_data.py
```

---

## Quick Reference

| Script | Input | Output | Time |
|--------|-------|--------|------|
| `collect_food_data.py` | API | `foodraw.txt` | 5-10 min |
| `cleanse_data.py` | `foodraw.txt` | `foodraw.xlsx` | < 1 min |
| `map_allergens.py` | `foodraw.xlsx` | `foodpreprocessed.xlsx` | < 1 min |

---

## Final Output

The `foodpreprocessed.xlsx` file is the final output that will be used as input for the mobile application.
