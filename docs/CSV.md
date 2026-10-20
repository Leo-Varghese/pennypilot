# CSV import/export

Required headers: `kind,amount,account_id,occurred_at`.
Optional: `currency,destination_id,category_id,merchant,payment_method,location,purpose,notes,tags,adjustment_direction`.

```csv
kind,amount,currency,account_id,occurred_at,merchant,payment_method,purpose
expense,125.50,INR,YOUR_ACCOUNT_ID,2026-10-10T12:30:00+05:30,Grocer,upi,Lunch supplies
```

Replace YOUR_ACCOUNT_ID with an account belonging to you. Use your category UUID for category_id, or omit it. Transfer rows require destination_id and no category. All related records must belong to the signed-in user. Money must be positive, at most 2 decimal places; adjustment_direction is 1 or -1. Timestamps need an explicit timezone offset. Payment methods: upi, cash, debit_card, credit_card, wallet, bank_transfer, other. Tags use a JSON string array, escaped according to CSV quoting rules.

UTF-8 (with or without BOM), at most 2 MiB and 5,000 rows. Any invalid row rolls back the whole import. Reimporting the exact same bytes returns 409; changing the file bypasses this exact-file protection, so review overlapping statements yourself. This is not bank-statement fuzzy deduplication.

Exports include a UTF-8 BOM for Excel and all transaction input fields, using account/category IDs for stable references. Spreadsheet-dangerous string prefixes are neutralized with a leading apostrophe. Such sanitized cells may need deliberate cleanup before reimport; exports are not a lossless restore format. Use full JSON export for exact data preservation. There is no automatic JSON restore endpoint in this version.
