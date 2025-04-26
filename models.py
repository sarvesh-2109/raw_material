from datetime import datetime
from pytz import timezone
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

IST = timezone('Asia/Kolkata')

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'employee'
    user_page_access = db.Column(db.Boolean, default=False)  # Permission to manage users
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'role': self.role,
            'user_page_access': self.user_page_access,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<User {self.user_id}>'

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_type = db.Column(db.String(20), nullable=False, default='supplier')
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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    
    def __repr__(self):
        return f'<Invoice {self.challan_bill_number}>'