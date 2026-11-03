# E-Commerce Web Scraping & ETL Pipeline

A Python-based Data Pipeline designed to scrape product data, transform and clean it using Pandas, and automatically load it into both CSV and SQLite database storage.

---

## 🛠️ ETL Architecture

The system is built using a **Modular Design** following the standard ETL architecture:

1. **Extract (`extract()`):**
   * Scrapes product listings across multiple categories (`laptops`, `phones`, `headphones`, `cameras`).
   * Iterates through product detail pages to retrieve real-time stock availability (`availability`).
   * Implements rate-limiting (`time.sleep(1)`) to avoid overloading the target server.

2. **Transform (`transform()`):**
   * **Price:** Extracts numeric floating-point values using Regular Expressions (`\d+\.\d+`) and rounds to 2 decimal places.
   * **Rating:** Maps star symbols (`★☆☆☆☆` – `★★★★★`) to numerical values (1–5) using dictionary mapping.
   * **Availability:** Cleans leading digits to standardize status strings (e.g., `in stock`).
   * **Data Validation:** Checks for duplicate entries based on `product_url` and identifies missing values (`NaN`).

3. **Load (`load()`):**
   * Exports cleaned data to `products.csv` (encoded with UTF-8 BOM for seamless Excel compatibility).
   * Persists data into an SQLite3 database under the `products` table (`ecommerce_products.db`).
   * Prints a structured **Execution Report** summarizing pipeline run metrics.

---

## 📂 Project Structure

```text
.
├── etl_v2.py                # Main ETL pipeline script
├── requirements.txt         # Third-party dependencies
├── products.csv             # Exported CSV data (generated after execution)
├── ecommerce_products.db    # SQLite database (generated after execution)
└── README.md                # Project documentation