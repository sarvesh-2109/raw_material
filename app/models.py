from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MaterialEntry(db.Model):
    __tablename__ = 'material_entries'

    id = db.Column(db.Integer, primary_key=True)
    sr_no = db.Column(db.Integer, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    vehicle_number = db.Column(db.String(12), nullable=False)
    supplier_name = db.Column(db.String(255), nullable=False)
    challan_bill_no = db.Column(db.String(100), nullable=False)
    material = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    basic_rate = db.Column(db.Float, nullable=False)
    amount_without_gst = db.Column(db.Float, nullable=False)

    # GST Columns
    cgst_2_5 = db.Column(db.Float, default=0)
    sgst_2_5 = db.Column(db.Float, default=0)
    cgst_6 = db.Column(db.Float, default=0)
    sgst_6 = db.Column(db.Float, default=0)
    cgst_9 = db.Column(db.Float, default=0)
    sgst_9 = db.Column(db.Float, default=0)
    cgst_14 = db.Column(db.Float, default=0)
    sgst_14 = db.Column(db.Float, default=0)
    igst_5 = db.Column(db.Float, default=0)
    igst_18 = db.Column(db.Float, default=0)
    
    cess = db.Column(db.Float, default=0)
    tds = db.Column(db.Float, default=0)

    # Transportation Columns
    transportation_charges = db.Column(db.Float, nullable=False)
    transportation_amount_without_gst = db.Column(db.Float, nullable=False)
    cgst_on_transportation = db.Column(db.Float, default=0)
    sgst_on_transportation = db.Column(db.Float, default=0)

    # Loading/Unloading Columns
    loading_unloading_amount = db.Column(db.Float, nullable=False)
    cgst_on_loading_unloading = db.Column(db.Float, default=0)
    sgst_on_loading_unloading = db.Column(db.Float, default=0)

    # Total Amounts
    total_amount_excluding_gst = db.Column(db.Float, nullable=False)
    total_gst_amount = db.Column(db.Float, nullable=False)
    total_amount_including_gst = db.Column(db.Float, nullable=False)