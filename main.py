import os
import glob
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment
from logger import (
    log_info, log_success, log_warning, log_error,
    print_header, print_summary_table,
    BOLD, RESET
)


def load_payout_summaries(data_dir):
    """
    Scans the data directory for Itemized_payouts CSV files,
    filters for 'payout' category, and returns a deduplicated DataFrame.
    """
    payout_files = glob.glob(os.path.join(data_dir, "Itemized_payouts_*.csv"))
    log_info(f"Found {len(payout_files)} payout summary files.")

    df_list = []
    for file in payout_files:
        df = pd.read_csv(file)
        # We only care about the master payout entry (category 'payout')
        df = df[df['reporting_category'] == 'payout']
        df_list.append(df)

    if not df_list:
        return pd.DataFrame()

    payouts_df = pd.concat(df_list, ignore_index=True)
    # Deduplicate in case overlapping date ranges were provided in CSVs
    payouts_df.drop_duplicates(
        subset=['payout_id'], keep='first', inplace=True)

    # Convert effective_at to datetime and sort chronologically
    payouts_df['effective_at'] = pd.to_datetime(payouts_df['effective_at'])
    payouts_df.sort_values(by='effective_at', inplace=True)

    return payouts_df


def load_reconciliation_data(data_dir):
    """
    Scans for reconciliation CSV files and returns a grouped object 
    indexed by automatic_payout_id.
    """
    reco_files = glob.glob(os.path.join(
        data_dir, "Itemized_payout_reconciliation_*.csv"))
    log_info(f"Found {len(reco_files)} reconciliation files.")

    df_list = [pd.read_csv(file) for file in reco_files]
    if not df_list:
        return pd.DataFrame(), None

    reco_df = pd.concat(df_list, ignore_index=True)
    # Grouping allows fast lookup of all transactions tied to a specific Stripe Payout ID
    reco_grouped = reco_df.groupby('automatic_payout_id')
    return reco_df, reco_grouped


def autofit_columns(ws):
    """
    Adjusts Excel column widths based on the maximum content length in each column.
    """
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        # Cap width to 50 to prevent extremely wide columns
        ws.column_dimensions[column].width = min(adjusted_width, 50)


def process_reports(data_dir, output_file):
    """
    Main processing pipeline: Loads CSVs, reconciles totals, and writes to a formatted Excel.
    """
    print_header("Starting Stripe Report Processing")
    log_info(f"Scanning directory: {BOLD}{data_dir}{RESET}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_info(f"Created results directory: {BOLD}{output_dir}{RESET}")

    payouts_df = load_payout_summaries(data_dir)
    reco_df, reco_grouped = load_reconciliation_data(data_dir)

    # Identifiy reconciliation columns dynamically from the source data
    if not reco_df.empty:
        # Include all columns
        reco_columns = [col for col in reco_df.columns]
    else:
        reco_columns = []

    # Initialize OpenPyXL Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Payouts Reconciliation"

    # Define headers: Summary headers (A-G) + Dynamic reconciliation headers
    payout_headers = ["Payout Date", "Payout ID", "Payout Status",
                      "Total Gross", "Total Fee", "Total Net", "Comments"]
    headers = payout_headers + reco_columns
    ws.append(headers)

    current_row = 2
    discrepancies_count = 0
    missing_reco_count = 0

    if payouts_df.empty:
        log_error("No payout data found.")
        return

    total_payouts = len(payouts_df)
    log_info(f"Processing {BOLD}{total_payouts}{RESET} payouts...")

    # Process each payout summary and match it with its reconciliation details
    for _, payout_row in payouts_df.iterrows():
        payout_id = payout_row['payout_id']
        payout_date = payout_row['effective_at']
        payout_status = payout_row['payout_status']
        payout_gross = float(payout_row['gross']) if pd.notna(
            payout_row['gross']) else 0.0
        payout_fee = float(payout_row['fee']) if pd.notna(
            payout_row['fee']) else 0.0
        payout_net = float(payout_row['net']) if pd.notna(
            payout_row['net']) else 0.0

        comments = []
        start_row = current_row

        # Check if we have reconciliation details for this payout
        if reco_grouped is not None and payout_id in reco_grouped.groups:
            payout_txns = reco_grouped.get_group(payout_id)

            # Verify if the sum of individual transactions matches the payout total
            # We round to 2 decimal places to handle floating point precision issues
            txn_net_sum = round(payout_txns['net'].sum(), 2)
            payout_net_rounded = round(payout_net, 2)

            if abs(txn_net_sum - payout_net_rounded) > 0.01:
                comments.append(
                    f"Net mismatch: Expected {payout_net_rounded}, Got {txn_net_sum}")

            if comments:
                discrepancies_count += 1

            comments_str = " | ".join(comments)

            # Write one row for each transaction tied to the payout
            for _, txn_row in payout_txns.iterrows():
                # Merge the left-side columns (Summary info)
                row_data = [str(payout_date), payout_id, payout_status,
                            payout_gross, payout_fee, payout_net, comments_str]
                # Append all available reconciliation columns dynamically
                for col in reco_columns:
                    val = txn_row[col]
                    row_data.append(val if pd.notna(val) else "")
                ws.append(row_data)
                current_row += 1

        else:
            # Handle case where summary exists but details are missing in reco files
            missing_reco_count += 1
            comments_str = "Missing reconciliation data"
            row_data = [str(payout_date), payout_id, payout_status,
                        payout_gross, payout_fee, payout_net, comments_str]
            row_data.extend([""] * len(reco_columns))
            ws.append(row_data)
            current_row += 1

        # Merge the payout summary cells (Columns A through G) for the group of transactions
        if current_row - 1 > start_row:
            end_row = current_row - 1
            for col_idx in range(1, 8):  # Col 1 (A) to Col 7 (G)
                ws.merge_cells(start_row=start_row, start_column=col_idx,
                               end_row=end_row, end_column=col_idx)
                cell = ws.cell(row=start_row, column=col_idx)
                cell.alignment = Alignment(vertical='top')

    # Apply final polish: Autofit columns
    autofit_columns(ws)

    wb.save(output_file)

    # --- Print Final Summary Report ---
    print_summary_table(total_payouts, missing_reco_count, discrepancies_count)
    log_success(f"Report successfully saved as: {BOLD}{output_file}{RESET}\n")


if __name__ == "__main__":
    DATA_DIR = "./data"
    OUTPUT_FILE = "./results/stripe_payout_report.xlsx"
    process_reports(DATA_DIR, OUTPUT_FILE)
