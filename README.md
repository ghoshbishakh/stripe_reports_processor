# stripe_reports_processor

This tool takes your Stripe payout exports and reconciliation logs and mashes them together into a single Excel sheet. It's basically a quick way to get your Stripe data into a format that a human (or your accountant) can actually read. 

It also double-checks that the transaction sums match the payout totals so you can spot mismatches easily.

## What reports do I need?
Go to your Stripe Dashboard (**Reports > Financial Reports**) and download these two **Itemized** reports:

1.  **Itemized Payouts**: Filename looks like `Itemized_payouts_*.csv`
2.  **Itemized Payout Reconciliation**: Filename looks like `Itemized_payout_reconciliation_*.csv`

Dump these CSV files into the `./data` folder before running anything.

## How to use it

```bash
# Set up a venv
python -m venv venv
source venv/bin/activate

# Install the two dependencies (pandas and openpyxl)
pip install -r requirements.txt

# Run the script
python main.py
```

The tool will scan your `./data` folder, do the math, and spit out a report in the `./results` folder.

## Where is the output?
Look for `./results/stripe_payout_report.xlsx`. 

The sheet has the payout summary on the left and all the detailed transactions on the right. If the net amounts don't add up correctly, it'll leave a note in the "Comments" column so you can check what's wrong.

## Project bits
- `main.py`: The core script.
- `logger.py`: Internal helpers for terminal logs.
- `data/`: Put your Stripe CSVs here.
- `results/`: Your finished Excel reports go here.
- `requirements.txt`: Just the packages needed to run this.
- `architecture/`: More technical details on how the data is processed.
