from datetime import datetime
from database import db

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    challan_bill_number = db.Column(db.String(50), nullable=False)
    material = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    basic_rate = db.Column(db.Float, nullable=False)
    amount_without_gst = db.Column(db.Float, nullable=False)
    
    # GST fields
    gst_type = db.Column(db.String(20), nullable=False)  # None, Intra-State, Inter-State
    cgst = db.Column(db.Float, default=0)
    sgst = db.Column(db.Float, default=0)
    igst = db.Column(db.Float, default=0)
    cess = db.Column(db.Float, default=0)
    tcs = db.Column(db.Float, default=0)
    
    # Transport fields
    transport_with_gst = db.Column(db.Boolean, default=True)
    transport_amount = db.Column(db.Float, default=0)
    transport_cgst = db.Column(db.Float, default=0)
    transport_sgst = db.Column(db.Float, default=0)
    transport_tds_percent = db.Column(db.Float, default=0)
    transport_tds_amount = db.Column(db.Float, default=0)
    transport_tds_deducted = db.Column(db.Float, default=0)
    
    # Loading/Unloading fields
    loading_with_gst = db.Column(db.Boolean, default=True)
    loading_amount = db.Column(db.Float, default=0)
    loading_cgst = db.Column(db.Float, default=0)
    loading_sgst = db.Column(db.Float, default=0)
    loading_tds_percent = db.Column(db.Float, default=0)
    loading_tds_amount = db.Column(db.Float, default=0)
    loading_tds_deducted = db.Column(db.Float, default=0)
    
    # Totals
    total_tds = db.Column(db.Float, nullable=False)
    total_cess = db.Column(db.Float, nullable=False)
    total_tcs = db.Column(db.Float, nullable=False)
    total_excluding_gst = db.Column(db.Float, nullable=False)
    total_gst_amount = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Invoice {self.challan_bill_number}>'