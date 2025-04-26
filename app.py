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
    'Hardener': {'cgst': 9, 'sgst': 9, 'igst': 18}
}

MATERIALS = list(MATERIAL_RATES.keys())
UNITS = ['MT', 'Kg', 'BRASS', 'TON', 'Ltr']
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


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/data-entry', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            vendor_type = request.form.get('vendor_type', 'supplier')
            
            # Process form data
            date_str = request.form['date']
            date = datetime.strptime(date_str, '%d/%m/%Y').date()
            
            vehicle_number = request.form['vehicle_number'].upper()
            if not validate_vehicle_number(vehicle_number):
                flash('Invalid vehicle number format', 'error')
                return redirect(url_for('index'))
            
            supplier_name = request.form['supplier_name']
            challan_bill_number = request.form['challan_bill_number']
            
            if vendor_type == 'supplier':
                # Process supplier fields
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
            else:  # transporter
                material = ""
                unit = ""
                quantity = 0.0
                basic_rate = 0.0
                amount_without_gst = 0.0
                gst_type = "None"
                cgst = sgst = igst = 0.0
                cess = 0.0
                tcs = 0.0
            
            
            
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
                vendor_type=vendor_type,
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


def get_filtered_invoices():
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    
    query = Invoice.query.order_by(Invoice.date.asc(), Invoice.id.asc())
    
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(Invoice.date >= from_date)
        except ValueError:
            flash('Invalid from date format', 'error')
    
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(Invoice.date <= to_date)
        except ValueError:
            flash('Invalid to date format', 'error')
    
    return query.all()


@app.route('/invoices')
def view_invoices():
    invoices = get_filtered_invoices()
    return render_template('invoices.html', invoices=invoices)


@app.route('/export_invoices')
def export_invoices():
    invoices = get_filtered_invoices()
    
    # Convert to pandas DataFrame
    data = []
    for index, invoice in enumerate(invoices, start=1):
        invoice_dict = {
            'Sr. No.': index,
            #'ID': invoice.id,
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


@app.route('/charts')
def charts_dashboard():
    # Get date range from query parameters or database
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    
    try:
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%d/%m/%Y').date()
        else:
            min_date = db.session.query(db.func.min(Invoice.date)).scalar()
            from_date = min_date if min_date else datetime.now().date()
        
        if to_date_str:
            to_date = datetime.strptime(to_date_str, '%d/%m/%Y').date()
        else:
            max_date = db.session.query(db.func.max(Invoice.date)).scalar()
            to_date = max_date if max_date else datetime.now().date()
    except:
        from_date = datetime.now().date() - timedelta(days=30)
        to_date = datetime.now().date()

    # Query data for the date range
    invoices = Invoice.query.filter(Invoice.date.between(from_date, to_date)).all()
    
    # Calculate total suppliers
    total_suppliers = db.session.query(db.func.count(db.func.distinct(Invoice.supplier_name))).scalar()
    
    # Calculate total purchases
    total_purchases = db.session.query(db.func.sum(Invoice.grand_total)).scalar() or 0
    
    # Deliveries by suppliers
    supplier_data = db.session.query(
        Invoice.supplier_name,
        db.func.sum(Invoice.amount_without_gst + Invoice.transport_amount + Invoice.loading_amount).label('total_amount')
    ).filter(
        Invoice.date.between(from_date, to_date),
        Invoice.vendor_type == 'supplier'
    ).group_by(
        Invoice.supplier_name
    ).order_by(
        db.func.sum(Invoice.amount_without_gst).desc()
    ).all()
    
    supplier_data = [{
        'supplier_name': item[0],
        'total_amount': float(item[1]) if item[1] else 0
    } for item in supplier_data]
    
    # Deliveries by transporters
    transporter_data = db.session.query(
        Invoice.supplier_name,
        db.func.sum(Invoice.transport_amount).label('total_amount')
    ).filter(
        Invoice.date.between(from_date, to_date),
        Invoice.vendor_type == 'transporter'
    ).group_by(
        Invoice.supplier_name
    ).order_by(
        db.func.sum(Invoice.transport_amount).desc()
    ).all()
    
    transporter_data = [{
        'transporter_name': item[0],
        'total_amount': float(item[1]) if item[1] else 0
    } for item in transporter_data]
    
    # Material distribution (by total value)
    material_data = db.session.query(
        Invoice.material,
        db.func.sum(Invoice.amount_without_gst).label('total_value'),
        db.func.count(Invoice.id).label('delivery_count')
    ).filter(
        Invoice.date.between(from_date, to_date),
        Invoice.vendor_type == 'supplier'
    ).group_by(
        Invoice.material
    ).order_by(
        db.func.sum(Invoice.amount_without_gst).desc()
    ).all()
    
    material_data = [{
        'material': item[0] if item[0] else 'Unknown',
        'total_value': float(item[1]) if item[1] else 0,
        'delivery_count': item[2]
    } for item in material_data]
    
    # Quantity vs Material by Unit
    quantity_by_unit_data = {}
    units_query = db.session.query(Invoice.unit).distinct().all()
    units = [unit[0] for unit in units_query if unit[0]]  # Filter out None/empty units
    
    for unit in units:
        unit_data = db.session.query(
            Invoice.material,
            db.func.sum(Invoice.quantity).label('total_quantity')
        ).filter(
            Invoice.date.between(from_date, to_date),
            Invoice.vendor_type == 'supplier',
            Invoice.unit == unit
        ).group_by(
            Invoice.material
        ).order_by(
            db.func.sum(Invoice.quantity).desc()
        ).all()
        
        quantity_by_unit_data[unit] = [{
            'material': item[0] if item[0] else 'Unknown',
            'total_quantity': float(item[1]) if item[1] else 0
        } for item in unit_data if item[1] > 0]  # Only include non-zero quantities

    amount_by_material_data = db.session.query(
        Invoice.material,
        db.func.sum(Invoice.amount_without_gst).label('total_amount_without_gst'),
        db.func.sum(Invoice.cgst + Invoice.sgst + Invoice.igst).label('total_gst_amount')
    ).filter(
        Invoice.date.between(from_date, to_date),
        Invoice.vendor_type == 'supplier'
    ).group_by(
        Invoice.material
    ).order_by(
        db.func.sum(Invoice.amount_without_gst).desc()
    ).all()

    amount_by_material_data = [{
        'material': item[0] if item[0] else 'Unknown',
        'total_amount_without_gst': float(item[1]) if item[1] else 0,
        'total_gst_amount': float(item[2]) if item[2] else 0,
        'total_amount_with_gst': float(item[1] + item[2]) if item[1] and item[2] is not None else float(item[1]) if item[1] else 0
    } for item in amount_by_material_data if item[1] > 0]

    # Add amount_by_material_data to the render_template call:
    return render_template('charts.html',
                        from_date=from_date.strftime('%d/%m/%Y'),
                        to_date=to_date.strftime('%d/%m/%Y'),
                        total_suppliers=total_suppliers,
                        total_purchases=total_purchases,
                        supplier_data=supplier_data,
                        transporter_data=transporter_data,
                        material_data=material_data,
                        quantity_by_unit_data=quantity_by_unit_data,
                        amount_by_material_data=amount_by_material_data)
    

@app.route('/edit_invoice/<int:invoice_id>', methods=['GET'])
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    date_str = invoice.date.strftime('%d/%m/%Y')
    return render_template('edit_invoice.html', 
                         invoice=invoice,
                         date_str=date_str,
                         materials=MATERIALS,
                         units=UNITS,
                         tcs_options=TCS_OPTIONS)

@app.route('/update_invoice/<int:invoice_id>', methods=['POST'])
def update_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        vendor_type = request.form.get('vendor_type', 'supplier')
        invoice.vendor_type = vendor_type
        
        # Process form data
        invoice.date = datetime.strptime(request.form['date'], '%d/%m/%Y').date()
        invoice.vehicle_number = request.form['vehicle_number'].upper()
        
        if not validate_vehicle_number(invoice.vehicle_number):
            flash('Invalid vehicle number format', 'error')
            return redirect(url_for('view_invoices'))
            
        invoice.supplier_name = request.form['supplier_name']
        invoice.challan_bill_number = request.form['challan_bill_number']
        
        if vendor_type == 'supplier':
            invoice.material = request.form['material']
            invoice.unit = request.form['unit']
            invoice.quantity = clean_number_input(request.form['quantity'])
            invoice.basic_rate = clean_number_input(request.form['basic_rate'])
            invoice.amount_without_gst = invoice.quantity * invoice.basic_rate
            
            invoice.gst_type = request.form['gst_type']
            invoice.cgst = invoice.sgst = invoice.igst = 0.0
            
            if invoice.gst_type == 'Intra-State':
                invoice.cgst = (invoice.amount_without_gst * MATERIAL_RATES[invoice.material]['cgst']) / 100
                invoice.sgst = (invoice.amount_without_gst * MATERIAL_RATES[invoice.material]['sgst']) / 100
            elif invoice.gst_type == 'Inter-State':
                invoice.igst = (invoice.amount_without_gst * MATERIAL_RATES[invoice.material]['igst']) / 100
                
            invoice.cess = clean_number_input(request.form['cess'])
            invoice.tcs = clean_number_input(request.form['tcs'])
        else:
            invoice.material = ""
            invoice.unit = ""
            invoice.quantity = 0.0
            invoice.basic_rate = 0.0
            invoice.amount_without_gst = 0.0
            invoice.gst_type = "None"
            invoice.cgst = invoice.sgst = invoice.igst = 0.0
            invoice.cess = 0.0
            invoice.tcs = 0.0
        
        # Transport Section
        invoice.transport_with_gst = request.form.get('transport_with_gst') == 'with'
        invoice.transport_amount = clean_number_input(request.form['transport_amount'])
        invoice.transport_cgst = invoice.transport_sgst = 0.0
        invoice.transport_tds_amount = 0.0
        
        if invoice.transport_with_gst:
            invoice.transport_cgst = (invoice.transport_amount * 2.5) / 100
            invoice.transport_sgst = (invoice.transport_amount * 2.5) / 100
        
        transport_tds_percent = clean_number_input(request.form['transport_tds'])
        if transport_tds_percent > 0:
            invoice.transport_tds_amount = (invoice.transport_amount * transport_tds_percent) / 100
            invoice.transport_tds_deducted = invoice.transport_amount - invoice.transport_tds_amount
        
        # Loading/Unloading Section
        invoice.loading_with_gst = request.form.get('loading_with_gst') == 'with'
        invoice.loading_amount = clean_number_input(request.form['loading_amount'])
        invoice.loading_cgst = invoice.loading_sgst = 0.0
        invoice.loading_tds_amount = 0.0
        
        if invoice.loading_with_gst:
            invoice.loading_cgst = (invoice.loading_amount * 9) / 100
            invoice.loading_sgst = (invoice.loading_amount * 9) / 100
        
        loading_tds_percent = clean_number_input(request.form['loading_tds'])
        if loading_tds_percent > 0:
            invoice.loading_tds_amount = (invoice.loading_amount * loading_tds_percent) / 100
            invoice.loading_tds_deducted = invoice.loading_amount - invoice.loading_tds_amount
        
        # Calculate totals
        invoice.total_tds = invoice.transport_tds_amount + invoice.loading_tds_amount
        invoice.total_cess = invoice.cess
        invoice.total_tcs = invoice.tcs
        
        invoice.total_gst_amount = (invoice.cgst + invoice.sgst + invoice.igst + 
                                    invoice.transport_cgst + invoice.transport_sgst + 
                                    invoice.loading_cgst + invoice.loading_sgst)
        
        invoice.total_excluding_gst = invoice.amount_without_gst + invoice.transport_amount + invoice.loading_amount
        invoice.grand_total = invoice.total_excluding_gst + invoice.total_gst_amount + invoice.total_cess + invoice.total_tcs
        
        db.session.commit()
        
        return '', 200  # Success response
    
    except Exception as e:
        db.session.rollback()
        return str(e), 400  # Error response

@app.route('/delete_invoices', methods=['POST'])
def delete_invoices():
    try:
        data = request.get_json()
        invoice_ids = data.get('invoice_ids', [])
        
        if not invoice_ids:
            return 'No invoices selected', 400
        
        # Delete the selected invoices
        Invoice.query.filter(Invoice.id.in_(invoice_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return '', 200  # Success response
    
    except Exception as e:
        db.session.rollback()
        return str(e), 400  # Error response
    
    
if __name__ == '__main__':
    app.run(debug=True)