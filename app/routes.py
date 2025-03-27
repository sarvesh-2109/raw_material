from flask import render_template, request, redirect, url_for, flash
from app.forms import MaterialEntryForm
from app.models import db, MaterialEntry
from app.utils import calculate_total_amounts, clean_numeric_input, convert_quantity_to_mt
from datetime import datetime

def init_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        form = MaterialEntryForm()
        
        if form.validate_on_submit():
            try:
                # Calculate total amounts and get all values
                total_amounts = calculate_total_amounts(form)
                
                # Create new material entry
                new_entry = MaterialEntry(
                    date=form.date.data,
                    vehicle_number=form.vehicle_number.data,
                    supplier_name=form.supplier_name.data,
                    challan_bill_no=form.challan_bill_no.data,
                    material=form.material.data,
                    unit=form.unit.data,
                    quantity=convert_quantity_to_mt(form.quantity.data, form.unit.data),
                    basic_rate=clean_numeric_input(form.basic_rate.data),
                    amount_without_gst=clean_numeric_input(form.amount_without_gst.data),
                    
                    # GST Columns
                    cgst_2_5=total_amounts['cgst_2_5'],
                    sgst_2_5=total_amounts['sgst_2_5'],
                    cgst_6=total_amounts['cgst_6'],
                    sgst_6=total_amounts['sgst_6'],
                    cgst_9=total_amounts['cgst_9'],
                    sgst_9=total_amounts['sgst_9'],
                    cgst_14=total_amounts['cgst_14'],
                    sgst_14=total_amounts['sgst_14'],
                    igst_5=total_amounts['igst_5'],
                    igst_18=total_amounts['igst_18'],
                    
                    cess=total_amounts['cess'],
                    tds=0,  # as per requirement
                    
                    # Transportation Columns
                    transportation_charges=clean_numeric_input(form.transportation_charges.data),
                    transportation_amount_without_gst=total_amounts['transportation_amount_without_gst'],
                    cgst_on_transportation=total_amounts['transportation_cgst'],
                    sgst_on_transportation=total_amounts['transportation_sgst'],
                    
                    # Loading/Unloading Columns
                    loading_unloading_amount=clean_numeric_input(form.loading_unloading_amount.data),
                    cgst_on_loading_unloading=total_amounts['loading_cgst'],
                    sgst_on_loading_unloading=total_amounts['loading_sgst'],
                    
                    # Total Amounts
                    total_amount_excluding_gst=total_amounts['total_amount_excluding_gst'],
                    total_gst_amount=total_amounts['total_gst_amount'],
                    total_amount_including_gst=total_amounts['total_amount_including_gst']
                )
                
                db.session.add(new_entry)
                db.session.commit()
                
                flash('Material entry added successfully!', 'success')
                return redirect(url_for('index'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding material entry: {str(e)}', 'error')
        
        # Set default date to today
        if not form.date.data:
            form.date.data = datetime.today()
        
        return render_template('index.html', form=form)