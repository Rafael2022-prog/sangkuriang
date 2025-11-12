#!/usr/bin/env python3
"""
Debug script untuk test tax calculation
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from compliance.tax_reporting_system import TaxReportingManager

async def debug_test():
    print("=== DEBUG TAX CALCULATION ===")
    
    # Create tax manager
    tax_manager = TaxReportingManager(storage_path="debug_test_reports")
    print(f"DEBUG: Created tax_manager: {type(tax_manager)}")
    print(f"DEBUG: Has calculate_monthly_tax: {hasattr(tax_manager, 'calculate_monthly_tax')}")
    
    # Process a transaction first
    transaction_data = {
        "user_id": "USER_001",
        "taxpayer_id": "NPWP_123456789",
        "taxpayer_type": "individual",
        "transaction_type": "crypto_sale",
        "amount_crypto": "0.05",
        "amount_idr": "47500000",
        "crypto_currency": "BTC",
        "transaction_date": "2024-01-15T10:00:00",
        "fees_idr": "25000",
        "description": "Sale of 0.05 BTC",
        "reference_number": "TXN-001",
        "location": "Jakarta",
        "payment_method": "bank_transfer"
    }
    
    print(f"DEBUG: Processing transaction...")
    result = await tax_manager.process_crypto_transaction(transaction_data)
    print(f"DEBUG: Transaction result: {result}")
    
    # Now calculate tax
    print(f"DEBUG: About to calculate monthly tax...")
    try:
        tax_result = await tax_manager.calculate_monthly_tax("NPWP_123456789", "2024-01")
        print(f"DEBUG: Tax calculation result: {tax_result}")
        print(f"DEBUG: Total tax payable: {tax_result.get('total_tax_payable', 'NOT_FOUND')}")
    except Exception as e:
        print(f"DEBUG: Exception during tax calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_test())