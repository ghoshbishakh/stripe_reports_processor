"""
Logging module for Stripe Report Processor.
Provides colorized terminal output using ANSI escape codes.
"""

# --- ANSI Color Constants ---
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log_info(message):
    """Logs an informational message in blue."""
    print(f"{BLUE}[INFO]{RESET} {message}")

def log_success(message):
    """Logs a success message in green."""
    print(f"{GREEN}[SUCCESS]{RESET} {message}")

def log_warning(message):
    """Logs a warning message in yellow."""
    print(f"{YELLOW}[WARNING]{RESET} {message}")

def log_error(message):
    """Logs an error message in red."""
    print(f"{RED}[ERROR]{RESET} {message}")

def print_header(message):
    """Prints a bold, cyan header for major processing steps."""
    print(f"\n{BOLD}{CYAN}# --- {message} --- #{RESET}\n")

def print_summary_table(total_payouts, missing_reco_count, discrepancies_count):
    """Prints a formatted summary table of the processing results."""
    print(f"\n{BOLD}{CYAN}# --- Processing Summary --- #{RESET}")
    print(f"{BOLD}{'Category':<30} | {'Count':>10}{RESET}")
    print(f"{'-'*30}-+-{'-'*10}")
    print(f"{'Total Payouts Processed':<30} | {total_payouts:>10}")
    
    missing_color = RED if missing_reco_count > 0 else GREEN
    print(f"{'Missing Reconciliation Data':<30} | {missing_color}{missing_reco_count:>10}{RESET}")
    
    discrepancy_color = RED if discrepancies_count > 0 else GREEN
    print(f"{'Discrepancies Found':<30} | {discrepancy_color}{discrepancies_count:>10}{RESET}")
    print(f"{'-'*43}")
