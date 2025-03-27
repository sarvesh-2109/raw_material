import re
from datetime import datetime

def clean_numeric_input(value):
    """
    Clean numeric input by removing commas and converting to float
    """
    if isinstance(value, str):
        # Remove commas and whitespace
        cleaned = re.sub(r'[,\s]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return float(value) if value is not None else 0.0

def convert_quantity_to_mt(quantity, unit):
    """
    Convert quantity to Metric Tons based on unit
    """
    quantity = clean_numeric_input(quantity)
    
    # Conversion factors
    unit_conversions = {
        'MT': 1.0,
        'Kg': 0.001,
        'BRASS': 0.25,  # Assuming BRASS is equivalent to MT
        'TON': 1.016,  # 1 Ton = 1.016 Metric Tons
        'Ltr': 0.001,  # Assuming liquid density similar to water
        'Bags': 0.04   # 1 bag = 40 kg = 0.04 MT
    }
    
    return quantity * unit_conversions.get(unit, 1.0)

def calculate_gst_amount(amount_without_gst, gst_rate):
    """
    Calculate GST amount based on rate
    """
    if gst_rate in ['None', '0%', None]:
        return 0.0
    
    # Remove % sign and convert to float
    rate = float(gst_rate.rstrip('%')) / 100
    return clean_numeric_input(amount_without_gst) * rate

def sanitize_tax_input(tax_input):
    """
    Sanitize tax input, return 0 if 'None' or empty
    """
    if not tax_input or tax_input == 'None':
        return 0.0
    
    # Remove % sign and convert to float
    return float(tax_input.rstrip('%')) / 100

def calculate_total_amounts(form_data):
    """
    Calculate total amounts based on form inputs
    """
    # Clean numeric inputs
    amount_without_gst = clean_numeric_input(form_data.amount_without_gst.data)
    transportation_charges = clean_numeric_input(form_data.transportation_charges.data)
    loading_unloading_amount = clean_numeric_input(form_data.loading_unloading_amount.data)
    
    # Calculate Transportation Amount
    transportation_amount_without_gst = convert_quantity_to_mt(
        form_data.quantity.data, 
        form_data.unit.data
    ) * transportation_charges
    
    # Calculate GST Amounts
    gst_amounts = {
        'cgst_2_5': calculate_gst_amount(amount_without_gst, form_data.cgst.data == '2.5%' and '2.5%' or '0%'),
        'sgst_2_5': calculate_gst_amount(amount_without_gst, form_data.sgst.data == '2.5%' and '2.5%' or '0%'),
        'cgst_6': calculate_gst_amount(amount_without_gst, form_data.cgst.data == '6%' and '6%' or '0%'),
        'sgst_6': calculate_gst_amount(amount_without_gst, form_data.sgst.data == '6%' and '6%' or '0%'),
        'cgst_9': calculate_gst_amount(amount_without_gst, form_data.cgst.data == '9%' and '9%' or '0%'),
        'sgst_9': calculate_gst_amount(amount_without_gst, form_data.sgst.data == '9%' and '9%' or '0%'),
        'cgst_14': calculate_gst_amount(amount_without_gst, form_data.cgst.data == '14%' and '14%' or '0%'),
        'sgst_14': calculate_gst_amount(amount_without_gst, form_data.sgst.data == '14%' and '14%' or '0%'),
        
        'igst_5': calculate_gst_amount(amount_without_gst, form_data.igst.data == '5%' and '5%' or '0%'),
        'igst_18': calculate_gst_amount(amount_without_gst, form_data.igst.data == '18%' and '18%' or '0%'),
        
        'cess': clean_numeric_input(form_data.cess.data or 0),
        'tds': 0  # Handled separately as per requirement
    }
    
    # Transportation GST (hardcoded 2.5%)
    transport_cgst = transportation_amount_without_gst * 0.025
    transport_sgst = transportation_amount_without_gst * 0.025
    
    # Loading/Unloading GST (hardcoded 9%)
    loading_cgst = 0
    loading_sgst = 0
    if form_data.loading_unloading_gst.data == 'with_gst':
        loading_cgst = loading_unloading_amount * 0.09
        loading_sgst = loading_unloading_amount * 0.09
    
    # Total GST Amount
    total_gst_amount = (
        sum(gst_amounts.values()) + 
        transport_cgst + transport_sgst + 
        loading_cgst + loading_sgst
    )
    
    # Total Amounts
    total_amount_excluding_gst = (
        amount_without_gst + 
        transportation_amount_without_gst + 
        loading_unloading_amount
    )
    
    total_amount_including_gst = (
        total_amount_excluding_gst + 
        total_gst_amount
    )
    
    return {
        **gst_amounts,
        'transportation_cgst': transport_cgst,
        'transportation_sgst': transport_sgst,
        'loading_cgst': loading_cgst,
        'loading_sgst': loading_sgst,
        'transportation_amount_without_gst': transportation_amount_without_gst,
        'total_gst_amount': total_gst_amount,
        'total_amount_excluding_gst': total_amount_excluding_gst,
        'total_amount_including_gst': total_amount_including_gst
    }