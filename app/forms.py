from flask_wtf import FlaskForm
from wtforms import (StringField, FloatField, SelectField, DateField, 
                     RadioField, SubmitField)
from wtforms.validators import DataRequired, Regexp, Optional

class MaterialEntryForm(FlaskForm):
    date = DateField('Date', format='%d/%m/%Y', validators=[DataRequired()])
    vehicle_number = StringField('Vehicle Number', validators=[
        DataRequired(), 
        Regexp(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$|^[A-Z]{2}\d{2}[A-Z]{1}\d{4}$', 
               message='Vehicle number must be in format XXNNXXNNNN or XXNNXNNNN')
    ])
    supplier_name = StringField('Supplier Name', validators=[DataRequired()])
    challan_bill_no = StringField('Challan/Bill Number', validators=[DataRequired()])
    
    # Material Dropdown with Search
    material = SelectField('Material', validators=[DataRequired()], choices=[
        'Cement', 'Lime Powder', 'Gypsum', 'Aluminium Powder', 
        'Soluble Oil', 'Mould Oil', 'DC Powder', 'Pond Ash', 
        'Biomass Briquette', 'Fly ash', 'Coal', 'Wood', 
        'Hardener', 'Mortar Bags'
    ])
    
    # Unit Dropdown with Search
    unit = SelectField('Unit', validators=[DataRequired()], choices=[
        'MT', 'Kg', 'BRASS', 'TON', 'Ltr', 'Bags'
    ])
    
    quantity = StringField('Quantity', validators=[DataRequired()])
    basic_rate = StringField('Basic Rate', validators=[DataRequired()])
    amount_without_gst = StringField('Amount Without GST', validators=[DataRequired()])
    
    # Tax Dropdowns
    sgst = SelectField('SGST', choices=[
        'None', '2.5%', '6%', '9%', '14%'
    ], validators=[Optional()])
    
    cgst = SelectField('CGST', choices=[
        'None', '2.5%', '6%', '9%', '14%'
    ], validators=[Optional()])
    
    igst = SelectField('IGST', choices=[
        'None', '5%', '18%'
    ], validators=[Optional()])
    
    cess = FloatField('CESS', validators=[Optional()])
    tds = SelectField('TDS', choices=[
        'None', '0.100'
    ], validators=[Optional()])
    
    transportation_charges = StringField('Transportation Charges', validators=[DataRequired()])
    loading_unloading_gst = RadioField('Loading/Unloading GST', 
                                       choices=[('with_gst', 'With GST'), 
                                                ('without_gst', 'Without GST')],
                                       default='without_gst')
    loading_unloading_amount = StringField('Loading/Unloading Amount', validators=[DataRequired()])
    
    submit = SubmitField('Submit')