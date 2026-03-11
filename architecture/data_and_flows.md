# Data and flows

This file contains information about the data files and the flow for processing the data.

1. All data files are located in `/data` directory.
2. All files are in `.csv` format.
 

## Itemized payouts data

1. Files with names starting with `Itemized_payouts_` are itemized payout data files.
2. The file names contain the date range for which the data is available in that file.
3. Each row represents one payout made from stripe to user's bank account.
4. The columns are: "payout_id","effective_at","currency","gross","fee","net","reporting_category","balance_transaction_id","description","payout_expected_arrival_date","payout_status"


## Payout reconciliation data

1. Files with names starting with `Itemized_payout_reconciliation_` are payout reconciliation data files.
2. These files contain a detailed breakdown of all balance transactions (charges, refunds, fees, etc.) that make up a specific payout.
3. The relationship between this data and the itemized payouts is established via the `automatic_payout_id` column, which corresponds to the `payout_id` in the itemized payouts data.
4. Key columns include:
    - `automatic_payout_id`: The ID of the payout this transaction belongs to.
    - `balance_transaction_id`: Unique ID for the balance transaction.
    - `gross`, `fee`, `net`: Financial details of the transaction.
    - `reporting_category`: Type of transaction (e.g., `charge`, `refund`, `fee`).
    - `customer_email`, `customer_name`: Customer details for charges.
    - `description`: A description of the transaction.
    - **And all other columns after this**

## Data Processing Flow

The objective of the application is to output an Excel file combining data from both types of CSV files. 

### Step-by-Step Processing

1.  **Scan Data Directory**: Identify all `Itemized_payouts_` and `Itemized_payout_reconciliation_` files in the `/data` directory.
2.  **Load Payouts**: 
    - Read all payout summary files.
    - Filter for `reporting_category == 'payout'`.
    - Handle duplicates across files if date ranges overlap.
3.  **Load Reconciliation Data**:
    - Read all reconciliation files.
    - Group balance transactions by `automatic_payout_id`.
4.  **Join and Reconcile**:
    - For each payout ID in the summary, find matching transactions in the reconciliation group.
    - If a payout has no reconciliation data in the provided files, mark it as "Unreconciled".
5.  **Generate Excel**:
    - For each payout, write a block of rows.
    - The left-hand columns (Payout Summary) should be merged across the rows corresponding to its transactions.

## Output Excel Structure

The final Excel file will contain a master sheet with the following mapping:

### Columns
- **Payout Summary (Left Side - Merged Cells)**:
    - `Payout Date` (`effective_at` from summary)
    - `Payout ID` (`payout_id`)
    - `Payout Status` (`payout_status`)
    - `Total Gross`, `Total Fee`, `Total Net`
    - `Comments` (for any discrepancies)
- **Transaction Details (Right Side)**:
    - `Transaction Date` (`created` from reconciliation)
    - `Transaction ID` (`balance_transaction_id`)
    - `Category` (`reporting_category`)
    - `Gross`, `Fee`, `Net`
    - `Customer Name`, `Customer Email`
    - `Description`

### Visual Example
| Payout Date | Payout ID | Total Net | Txn ID | Category | Txn Net | Customer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2025-04-02 | po_1R99d... | 54426.86 | txn_3R5ART... | charge | 2423.82 | Alejandro Flores |
| (merged) | (merged) | (merged) | txn_3R5AZ7... | charge | 2438.74 | Neil Sweeney |
| **Total** | | **54426.86** | | | **4862.56** | (Intermediary sum) |

*Note: The sum of transaction 'Net' columns for a payout should ideally match the Payout 'Net' value, minus any external adjustments. If they do not match, write it in the comments column.*
