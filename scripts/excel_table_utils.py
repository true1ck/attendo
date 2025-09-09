#!/usr/bin/env python3
"""
Excel Table Utils - Wrapper Functions
Provides simple wrapper functions that maintain table structure when updating Excel files.
These functions can be used as drop-in replacements for pandas.DataFrame.to_excel() 
to ensure all Excel files maintain proper table formatting.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
import logging
from excel_table_formatter import (
    update_notification_table, 
    create_notification_table,
    save_dataframe_as_table,
    validate_notification_table,
    excel_table_formatter
)

# Configure logging
logger = logging.getLogger(__name__)

def to_excel_with_table(df: pd.DataFrame, 
                       excel_writer: Union[str, Path],
                       sheet_name: str = 'Sheet1',
                       table_name: Optional[str] = None,
                       table_style: str = 'TableStyleMedium9',
                       index: bool = False,
                       **kwargs) -> bool:
    """
    Enhanced version of pandas DataFrame.to_excel() that creates proper Excel tables.
    
    This function can be used as a drop-in replacement for DataFrame.to_excel()
    with the added benefit of creating properly formatted tables.
    
    Args:
        df: pandas DataFrame to save
        excel_writer: File path or ExcelWriter object
        sheet_name: Name of the worksheet
        table_name: Name for the Excel table (auto-generated if None)
        table_style: Excel table style
        index: Whether to include DataFrame index (ignored, always False for tables)
        **kwargs: Additional arguments (for compatibility with pandas.to_excel)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert excel_writer to string if it's a Path object
        filepath = str(excel_writer)
        
        # Generate table name if not provided
        if table_name is None:
            # Extract base name from file path for table name
            base_name = Path(filepath).stem.replace('-', '_').replace(' ', '_')
            table_name = f"{base_name}_Table"
        
        # Use our table formatter to save the file
        success = save_dataframe_as_table(
            df=df,
            filepath=filepath,
            table_name=table_name,
            sheet_name=sheet_name,
            table_style=table_style
        )
        
        if success:
            logger.info(f"✅ Successfully saved DataFrame to Excel table: {filepath}")
        else:
            logger.error(f"❌ Failed to save DataFrame to Excel table: {filepath}")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Error in to_excel_with_table: {str(e)}")
        return False

def update_excel_table(df: pd.DataFrame, 
                      filepath: Union[str, Path],
                      notification_type: Optional[str] = None,
                      backup: bool = True,
                      **kwargs) -> bool:
    """
    Update an existing Excel file while preserving table structure.
    
    Args:
        df: pandas DataFrame with updated data
        filepath: Path to the Excel file to update
        notification_type: Type of notification if this is a notification file
        backup: Whether to create a backup before updating
        **kwargs: Additional arguments for compatibility
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        
        # If notification_type is provided, use the notification table updater
        if notification_type:
            return update_notification_table(df, notification_type, backup)
        
        # Otherwise, determine table configuration from file
        # Try to load existing file to get table info
        config_type = None
        
        # Try to match the filename to known notification types
        filename = filepath.name.lower()
        if 'daily_status_reminders' in filename or 'daily_reminders' in filename:
            config_type = 'daily_reminders'
        elif 'manager_summary' in filename:
            config_type = 'manager_summary'
        elif 'late_submission' in filename:
            config_type = 'late_submissions'
        elif 'mismatch' in filename:
            config_type = 'mismatch_alerts'
        elif 'manager_feedback' in filename:
            config_type = 'manager_feedback'
        elif 'monthly_report' in filename:
            config_type = 'monthly_reports'
        elif 'admin' in filename and 'alert' in filename:
            config_type = 'admin_alerts'
        elif 'holiday' in filename:
            config_type = 'holiday_reminders'
        elif 'billing' in filename:
            config_type = 'billing_corrections'
        
        # Use the table formatter with detected or provided config
        success = excel_table_formatter.update_excel_table_from_dataframe(
            df=df,
            filepath=str(filepath),
            config_type=config_type,
            backup=backup
        )
        
        if success:
            logger.info(f"✅ Successfully updated Excel table: {filepath}")
        else:
            logger.error(f"❌ Failed to update Excel table: {filepath}")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Error in update_excel_table: {str(e)}")
        return False

def validate_excel_table(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate that an Excel file has proper table structure.
    
    Args:
        filepath: Path to the Excel file to validate
        
    Returns:
        dict: Validation results with detailed information
    """
    try:
        filepath = Path(filepath)
        
        # Determine notification type if possible
        filename = filepath.name.lower()
        notification_type = None
        
        if 'daily_status_reminders' in filename or 'daily_reminders' in filename:
            notification_type = 'daily_reminders'
        elif 'manager_summary' in filename:
            notification_type = 'manager_summary'
        elif 'late_submission' in filename:
            notification_type = 'late_submissions'
        # Add more mappings as needed
        
        if notification_type:
            # Use notification-specific validation
            return validate_notification_table(notification_type)
        else:
            # Use generic table validation
            return excel_table_formatter.validate_table_structure(str(filepath))
            
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'filepath': str(filepath)
        }

def ensure_all_excel_files_have_tables(directory: Union[str, Path] = "notification_configs") -> Dict[str, bool]:
    """
    Ensure all Excel files in a directory have proper table formatting.
    
    Args:
        directory: Directory path to process
        
    Returns:
        dict: Results for each file processed
    """
    results = {}
    directory = Path(directory)
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return results
    
    # Find all Excel files
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xls"))
    
    for excel_file in excel_files:
        try:
            logger.info(f"Processing {excel_file.name}...")
            
            # Skip backup files
            if excel_file.name.startswith('backup_') or excel_file.name.startswith('PA_backup_'):
                logger.info(f"Skipping backup file: {excel_file.name}")
                results[excel_file.name] = True
                continue
            
            # Read the Excel file
            df = pd.read_excel(excel_file)
            
            # Update it with table formatting
            success = update_excel_table(df, excel_file, backup=True)
            results[excel_file.name] = success
            
            if success:
                logger.info(f"✅ Successfully ensured table format for: {excel_file.name}")
            else:
                logger.error(f"❌ Failed to ensure table format for: {excel_file.name}")
                
        except Exception as e:
            logger.error(f"❌ Error processing {excel_file.name}: {str(e)}")
            results[excel_file.name] = False
    
    return results

def batch_validate_excel_tables(directory: Union[str, Path] = "notification_configs") -> Dict[str, Dict]:
    """
    Validate all Excel files in a directory for proper table structure.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        dict: Validation results for each file
    """
    results = {}
    directory = Path(directory)
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return results
    
    # Find all Excel files
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xls"))
    
    for excel_file in excel_files:
        try:
            # Skip backup files
            if excel_file.name.startswith('backup_') or excel_file.name.startswith('PA_backup_'):
                continue
                
            validation = validate_excel_table(excel_file)
            results[excel_file.name] = validation
            
        except Exception as e:
            results[excel_file.name] = {
                'valid': False,
                'error': str(e)
            }
    
    return results

# Monkey patch pandas DataFrame to add table functionality (optional)
def add_table_method_to_dataframe():
    """
    Add a to_excel_table method to pandas DataFrame for easy access.
    This is optional and can be called if you want DataFrame.to_excel_table() functionality.
    """
    def to_excel_table(self, excel_writer, sheet_name='Sheet1', table_name=None, 
                      table_style='TableStyleMedium9', **kwargs):
        """Add to_excel_table method to DataFrame"""
        return to_excel_with_table(
            df=self,
            excel_writer=excel_writer,
            sheet_name=sheet_name,
            table_name=table_name,
            table_style=table_style,
            **kwargs
        )
    
    # Add the method to DataFrame
    pd.DataFrame.to_excel_table = to_excel_table
    logger.info("✅ Added to_excel_table method to pandas DataFrame")

# Convenience aliases for backward compatibility
excel_with_table = to_excel_with_table
update_excel_with_table = update_excel_table

if __name__ == "__main__":
    # Test the utilities
    print("🧪 Testing Excel Table Utils...")
    
    # Create test data
    test_data = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'Email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'david@test.com', 'eve@test.com'],
        'Department': ['Engineering', 'Sales', 'Marketing', 'Engineering', 'Sales'],
        'Status': ['Active', 'Active', 'Pending', 'Active', 'Inactive'],
        'Date': ['2025-01-09'] * 5
    })
    
    test_file = "test_table_utils.xlsx"
    
    # Test creating Excel with table
    print("Testing to_excel_with_table...")
    success = to_excel_with_table(
        test_data, 
        test_file, 
        sheet_name='Test_Data',
        table_name='TestUtilsTable'
    )
    
    if success:
        print("✅ Successfully created Excel file with table format")
        
        # Test validation
        print("Testing validation...")
        validation = validate_excel_table(test_file)
        if validation.get('valid', False):
            print(f"✅ Table validation passed: {validation}")
        else:
            print(f"❌ Table validation failed: {validation}")
        
        # Test updating
        print("Testing update...")
        updated_data = test_data.copy()
        updated_data['Status'] = 'Updated'
        
        update_success = update_excel_table(updated_data, test_file, backup=True)
        if update_success:
            print("✅ Successfully updated Excel file")
        else:
            print("❌ Failed to update Excel file")
        
        # Clean up
        try:
            os.remove(test_file)
            # Also remove any backup files
            for backup_file in Path('.').glob(f"backup_*{test_file}"):
                os.remove(backup_file)
            print("🧹 Cleaned up test files")
        except:
            pass
    else:
        print("❌ Failed to create Excel file with table format")
    
    print("✅ Excel Table Utils testing completed!")
