from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta  
from config import Config
from models import Invoice
from database import db, init_db
from flask import send_file
import pandas as pd
from io import BytesIO
from flask import jsonify
import math
import re

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db(app)
migrate = Migrate(app, db)

# Material GST rates
MATERIAL_RATES = {
    'Cement': {'cgst': 14, 'sgst': 14, 'igst': 28},
    'Lime Powder': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Gypsum': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Aluminium Powder': {'cgst': 9, 'sgst': 9, 'igst': 18},
    'Soluble Oil': {'cgst': 9, 'sgst': 9, 'igst': 18},
    'Mould Oil': {'cgst': 9, 'sgst': 9, 'igst': 18},
    'DC Powder': {'cgst': 9, 'sgst': 9, 'igst': 18},
    'Pond Ash': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Biomass Briquette': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Fly Ash': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Coal': {'cgst': 2.5, 'sgst': 2.5, 'igst': 5},
    'Wood': {'cgst': 0, 'sgst': 0, 'igst': 0},
    'Hardener': {'cgst': 9, 'sgst': 9, 'igst': 18},
    'Mortar Bags': {'cgst': 9, 'sgst': 9, 'igst': 18}
}

MATERIALS = list(MATERIAL_RATES.keys())
UNITS = ['MT', 'Kg', 'BRASS', 'TON', 'Ltr', 'Bags']
TCS_OPTIONS = ['None', '0.100']

def clean_number_input(value):
    """Remove commas and convert to float"""
    if not value:
        return 0.0
    return float(str(value).replace(',', ''))

def validate_vehicle_number(vehicle_no):
    """Validate vehicle number format"""
    pattern1 = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$')
    pattern2 = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}$')
    return bool(pattern1.match(vehicle_no)) or bool(pattern2.match(vehicle_no))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Process form data
            date_str = request.form['date']
            date = datetime.strptime(date_str, '%d/%m/%Y').date()
            
            vehicle_number = request.form['vehicle_number'].upper()
            if not validate_vehicle_number(vehicle_number):
                flash('Invalid vehicle number format', 'error')
                return redirect(url_for('index'))
            
            supplier_name = request.form['supplier_name']
            challan_bill_number = request.form['challan_bill_number']
            material = request.form['material']
            unit = request.form['unit']
            
            quantity = clean_number_input(request.form['quantity'])
            basic_rate = clean_number_input(request.form['basic_rate'])
            amount_without_gst = quantity * basic_rate
            
            # GST Section
            gst_type = request.form['gst_type']
            cgst = sgst = igst = 0.0
            
            if gst_type == 'Intra-State':
                cgst = (amount_without_gst * MATERIAL_RATES[material]['cgst']) / 100
                sgst = (amount_without_gst * MATERIAL_RATES[material]['sgst']) / 100
            elif gst_type == 'Inter-State':
                igst = (amount_without_gst * MATERIAL_RATES[material]['igst']) / 100
            
            cess = clean_number_input(request.form['cess'])
            tcs = clean_number_input(request.form['tcs'])
            
            # Transport Section
            transport_with_gst = request.form.get('transport_with_gst') == 'with'
            transport_amount = clean_number_input(request.form['transport_amount'])
            transport_cgst = transport_sgst = transport_tds = 0.0
            transport_tds_amount = 0.0
            
            if transport_with_gst:
                transport_cgst = (transport_amount * 2.5) / 100
                transport_sgst = (transport_amount * 2.5) / 100
            
            transport_tds_percent = clean_number_input(request.form['transport_tds'])
            if transport_tds_percent > 0:
                transport_tds_amount = (transport_amount * transport_tds_percent) / 100
                transport_tds = transport_amount - transport_tds_amount
            
            # Loading/Unloading Section
            loading_with_gst = request.form.get('loading_with_gst') == 'with'
            loading_amount = clean_number_input(request.form['loading_amount'])
            loading_cgst = loading_sgst = loading_tds = 0.0
            loading_tds_amount = 0.0
            
            if loading_with_gst:
                loading_cgst = (loading_amount * 9) / 100
                loading_sgst = (loading_amount * 9) / 100
            
            loading_tds_percent = clean_number_input(request.form['loading_tds'])
            if loading_tds_percent > 0:
                loading_tds_amount = (loading_amount * loading_tds_percent) / 100
                loading_tds = loading_amount - loading_tds_amount
            
            # Calculate totals
            total_tds_amount = transport_tds_amount + loading_tds_amount
            total_cess = cess
            total_tcs = tcs
            
            total_gst_amount = (cgst + sgst + igst + 
                                transport_cgst + transport_sgst + 
                                loading_cgst + loading_sgst)
            
            total_excluding_gst = amount_without_gst + transport_amount + loading_amount
            grand_total = total_excluding_gst + total_gst_amount + total_cess + total_tcs
            
            # Create new invoice
            new_invoice = Invoice(
                date=date,
                vehicle_number=vehicle_number,
                supplier_name=supplier_name,
                challan_bill_number=challan_bill_number,
                material=material,
                unit=unit,
                quantity=quantity,
                basic_rate=basic_rate,
                amount_without_gst=amount_without_gst,
                gst_type=gst_type,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                cess=cess,
                tcs=tcs,
                transport_with_gst=transport_with_gst,
                transport_amount=transport_amount,
                transport_cgst=transport_cgst,
                transport_sgst=transport_sgst,
                transport_tds_percent=transport_tds_percent,
                transport_tds_amount=transport_tds_amount,
                transport_tds_deducted=transport_tds,
                loading_with_gst=loading_with_gst,
                loading_amount=loading_amount,
                loading_cgst=loading_cgst,
                loading_sgst=loading_sgst,
                loading_tds_percent=loading_tds_percent,
                loading_tds_amount=loading_tds_amount,
                loading_tds_deducted=loading_tds,
                total_tds=total_tds_amount,
                total_cess=total_cess,
                total_tcs=total_tcs,
                total_excluding_gst=total_excluding_gst,
                total_gst_amount=total_gst_amount,
                grand_total=grand_total
            )
            
            db.session.add(new_invoice)
            db.session.commit()
            
            flash('Invoice saved successfully!', 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving invoice: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    # For GET request, show form with today's date
    today = datetime.now().strftime('%d/%m/%Y')
    return render_template('index.html', 
                         today=today, 
                         materials=MATERIALS, 
                         units=UNITS, 
                         tcs_options=TCS_OPTIONS)


@app.route('/invoices')
def view_invoices():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('invoices.html', invoices=invoices)


@app.route('/export_invoices')
def export_invoices():
    # Query all invoices
    invoices = Invoice.query.all()
    
    # Convert to pandas DataFrame
    data = []
    for invoice in invoices:
        invoice_dict = {
            'ID': invoice.id,
            'Date': invoice.date.strftime('%d/%m/%Y'),
            'Vehicle Number': invoice.vehicle_number,
            'Supplier Name': invoice.supplier_name,
            'Challan/Bill Number': invoice.challan_bill_number,
            'Material': invoice.material,
            'Unit': invoice.unit,
            'Quantity': invoice.quantity,
            'Basic Rate': invoice.basic_rate,
            'Amount Without GST': invoice.amount_without_gst,
            'GST Type': invoice.gst_type,
            'CGST': invoice.cgst,
            'SGST': invoice.sgst,
            'IGST': invoice.igst,
            'CESS': invoice.cess,
            'TCS': invoice.tcs,
            'Transport Amount': invoice.transport_amount,
            'Transport CGST': invoice.transport_cgst,
            'Transport SGST': invoice.transport_sgst,
            'Transport TDS %': invoice.transport_tds_percent,
            'Transport TDS Amount': invoice.transport_tds_amount,
            'Loading Amount': invoice.loading_amount,
            'Loading CGST': invoice.loading_cgst,
            'Loading SGST': invoice.loading_sgst,
            'Loading TDS %': invoice.loading_tds_percent,
            'Loading TDS Amount': invoice.loading_tds_amount,
            'Total TDS': invoice.total_tds,
            'Total CESS': invoice.total_cess,
            'Total TCS': invoice.total_tcs,
            'Total Excluding GST': invoice.total_excluding_gst,
            'Total GST Amount': invoice.total_gst_amount,
            'Grand Total': invoice.grand_total,
            'Created At': invoice.created_at.strftime('%d/%m/%Y %H:%M:%S')
        }
        data.append(invoice_dict)
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Invoices', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Invoices']
        
        # Add a format for the header
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths based on content
        for i, column in enumerate(df.columns):
            max_len = max(
                df[column].astype(str).map(len).max(),  # Max length in column
                len(str(column))  # Length of column header
            ) + 2  # Add a little extra space
            
            # Cap the maximum width at 50 to prevent extremely wide columns
            worksheet.set_column(i, i, min(max_len, 50))
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='invoices_export.xlsx'
    )
    
    
@app.template_filter('format_currency')
def format_currency(value):
    if value is None:
        return "0.00"
    if value >= 1e7:  # Crores
        return f"₹{value/1e7:.2f} Cr"
    elif value >= 1e5:  # Lakhs
        return f"₹{value/1e5:.2f} L"
    else:
        return f"₹{value:,.2f}"

# Add this route after the existing routes
@app.route('/charts')
def charts_dashboard():
    # Get date range from query parameters or database
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    
    try:
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%d/%m/%Y').date()
        else:
            # Get min date from database
            min_date = db.session.query(db.func.min(Invoice.date)).scalar()
            from_date = min_date if min_date else datetime.now().date()
        
        if to_date_str:
            to_date = datetime.strptime(to_date_str, '%d/%m/%Y').date()
        else:
            # Get max date from database
            max_date = db.session.query(db.func.max(Invoice.date)).scalar()
            to_date = max_date if max_date else datetime.now().date()
    except:
        # Fallback to default dates if parsing fails
        from_date = datetime.now().date() - timedelta(days=30)
        to_date = datetime.now().date()

    # Query data for the date range
    invoices = Invoice.query.filter(Invoice.date.between(from_date, to_date)).all()
    
    # Calculate total suppliers
    total_suppliers = db.session.query(db.func.count(db.func.distinct(Invoice.supplier_name))).scalar()
    
    # Calculate total purchases
    total_purchases = db.session.query(db.func.sum(Invoice.grand_total)).scalar() or 0
    
    # Get deliveries by suppliers data
    deliveries_data = db.session.query(
        Invoice.supplier_name,
        db.func.count(Invoice.id).label('delivery_count'),
        db.func.sum(Invoice.grand_total).label('total_amount')
    ).filter(
        Invoice.date.between(from_date, to_date)
    ).group_by(
        Invoice.supplier_name
    ).order_by(
        db.func.count(Invoice.id).desc()
    ).all()
    
    # Convert to dictionary format for JSON
    deliveries_data = [{
        'supplier_name': item[0],
        'delivery_count': item[1],
        'total_amount': float(item[2]) if item[2] else 0
    } for item in deliveries_data]
    
    return render_template('charts.html',
                         from_date=from_date.strftime('%d/%m/%Y'),
                         to_date=to_date.strftime('%d/%m/%Y'),
                         total_suppliers=total_suppliers,
                         total_purchases=total_purchases,
                         deliveries_data=deliveries_data)
    
    
if __name__ == '__main__':
    app.run(debug=True)