from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from config import Config
from models import Invoice
from database import db, init_db
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
            total_including_gst = total_excluding_gst + total_gst_amount
            
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
                total_including_gst=total_including_gst
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

if __name__ == '__main__':
    app.run(debug=True)