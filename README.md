
# 📘 LedgerLens

LedgerLens is a receipt-tracking web application where users can upload their purchase receipts. The app uses **Claude Sonnet 3.5** to extract relevant data from the uploaded image/PDF, stores the structured data in **Amazon DynamoDB**, and displays the receipts on a dashboard — including automatic **total spending calculation**.

---

## 🚀 Features

- 🧾 Upload receipt (image or PDF)
- 🤖 Extract data using Claude Sonnet 3.5 (via API)
- ☁️ Save extracted info to AWS DynamoDB
- 📊 Display list of receipts and total spending
- 🔒 Lightweight Flask backend with secure endpoints

---

## 🧱 Tech Stack

- **Backend**: Python + Flask  
- **AI Extraction**: Claude Sonnet 3.5 (Anthropic API)  
- **Database**: Amazon DynamoDB  
- **Storage**: Amazon S3 (optional for storing uploaded files)  
- **Deployment**: AWS Lambda / EC2 / Fargate (flexible)  

---

## 📂 Project Structure

```
ledgerlens/
│
├── app/
│   ├── __init__.py
│   └── routes.py
│
├── templates/
│   └── upload.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── upload.js
│
├── lambda/
│   ├── extract_lambda.py
│   └── prompt.py
│
├── .env
├── app.py
├── requirements.txt
├── README.md
```

---

## ⚙️ How It Works

1. **User Upload**  
   User uploads a receipt (image or PDF) via web UI or API.

2. **Claude Sonnet Extraction**  
   The file is passed to Claude Sonnet 3.5 using a prompt to extract:
   - Vendor name  
   - Date  
   - Items  
   - Amounts  
   - Total  

3. **Data Processing**  
   The structured data returned is parsed and validated.

4. **DynamoDB Storage**  
   The receipt data is saved in a DynamoDB table:
   ```json
   {
     "receipt_id": "uuid",
     "vendor": "Starbucks",
     "date": "2025-07-01",
     "items": [...],
     "total": 24.90
   }
   ```

5. **Frontend Display**  
   The dashboard lists all uploaded receipts and displays the total spending.

---

## 🛠️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/yourname/ledgerlens.git
cd ledgerlens
```

### 2. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure AWS

Make sure your AWS credentials are configured properly to access DynamoDB and optionally S3.

### 4. Configure Claude API

Add your Claude API key to a `.env` file:

```env
CLAUDE_API_KEY=your_anthropic_key_here
```

### 5. Run Flask server

```bash
flask run
```

---

## 🧪 Sample Claude Prompt (for receipt extraction)

```
Extract the following from this receipt image:
- Vendor name
- Date of purchase
- List of items (name, price)
- Total amount

Return the result as JSON:
{
  "vendor": "",
  "date": "",
  "items": [{"name": "", "price": float}],
  "total": float
}
```

---

## 📈 Example Output (Saved to DynamoDB)

```json
{
  "receipt_id": "123e4567-e89b-12d3-a456-426614174000",
  "vendor": "7-Eleven",
  "date": "2025-06-30",
  "items": [
    {"name": "Coca Cola", "price": 2.00},
    {"name": "Bread", "price": 3.50}
  ],
  "total": 5.50
}
```

---

## ✅ Future Improvements

- User authentication & login  
- Spending category tagging (e.g., Food, Grocery)  
- Monthly reports  
- Mobile-friendly UI  
- Export data (CSV, PDF)

---

## 📄 License

MIT License

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you’d like to change.
