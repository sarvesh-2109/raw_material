$(document).ready(function() {
    // Initialize Select2 and Datepicker
    $('.select2').select2({ width: '100%' });
    $('#date').datepicker({ 
        format: 'dd/mm/yyyy', 
        autoclose: true, 
        todayHighlight: true 
    });

    // Material GST rates
    const MATERIAL_RATES = {
        'Cement': {cgst: 14, sgst: 14, igst: 28},
        'Lime Powder': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Gypsum': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Aluminium Powder': {cgst: 9, sgst: 9, igst: 18},
        'Soluble Oil': {cgst: 9, sgst: 9, igst: 18},
        'Mould Oil': {cgst: 9, sgst: 9, igst: 18},
        'DC Powder': {cgst: 9, sgst: 9, igst: 18},
        'Pond Ash': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Biomass Briquette': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Fly Ash': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Coal': {cgst: 2.5, sgst: 2.5, igst: 5},
        'Wood': {cgst: 0, sgst: 0, igst: 0},
        'Hardener': {cgst: 9, sgst: 9, igst: 18},
        'Mortar Bags': {cgst: 9, sgst: 9, igst: 18}
    };

    // Set up event handlers for all input fields
    function setupEventHandlers() {
        // Quantity and Basic Rate - Update on ANY input change (keypress, paste, etc.)
        $('#quantity, #basic_rate').on('input keyup', function() {
            calculateAmountWithoutGST();
            calculateGST();
            calculateTotals();
        });

        // Material and GST Type - Update immediately on change
        $('#material').on('change', function() {
            calculateGST();
            calculateTotals();
        });
        
        $('input[name="gst_type"]').on('change', function() {
            calculateGST();
            calculateTotals();
        });

        // Transport Section - Update on input/keyup
        $('#transport_amount').on('input keyup', function() {
            calculateTransportGST();
            calculateTotals();
        });
        
        $('input[name="transport_with_gst"]').on('change', function() {
            calculateTransportGST();
            calculateTotals();
        });

        // Loading Section - Update on input/keyup
        $('#loading_amount').on('input keyup', function() {
            calculateLoadingGST();
            calculateTotals();
        });
        
        $('input[name="loading_with_gst"]').on('change', function() {
            calculateLoadingGST();
            calculateTotals();
        });

        // Other fields (CESS, TCS, TDS) - Update on input/keyup
        $('#cess, #tcs, #transport_tds, #loading_tds').on('input keyup', calculateTotals);

        // Vehicle number uppercase (unchanged)
        $('#vehicle_number').on('input', function() {
            this.value = this.value.toUpperCase();
            validateVehicleNumber();
        });
    }

    // Form validation before submission (unchanged)
    $('#invoiceForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: $('.is-invalid').first().offset().top - 100
            }, 500);
        }
    });



// VALIDATION FUNCTIONS
function validateVehicleNumber() {
    const vehicleNo = $('#vehicle_number').val();
    const pattern1 = /^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$/;
    const pattern2 = /^[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}$/;
    
    if (vehicleNo && !pattern1.test(vehicleNo) && !pattern2.test(vehicleNo)) {
        $('#vehicle_number').addClass('is-invalid');
        return false;
    } else {
        $('#vehicle_number').removeClass('is-invalid');
        return true;
    }
}

function validateForm() {
    let isValid = true;
    
    // Validate all required fields
    $('input[required], select[required]').each(function() {
        if (!$(this).val()) {
            isValid = false;
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });
    
    // Special validation for vehicle number
    if (!validateVehicleNumber()) {
        isValid = false;
    }
    
    // Validate quantity and rate are positive numbers
    if (cleanNumberInput($('#quantity').val()) <= 0) {
        $('#quantity').addClass('is-invalid');
        isValid = false;
    }
    
    if (cleanNumberInput($('#basic_rate').val()) <= 0) {
        $('#basic_rate').addClass('is-invalid');
        isValid = false;
    }
    
    if (!isValid) {
        $('#form-error').removeClass('d-none').text('Please fill all required fields with valid values!');
    } else {
        $('#form-error').addClass('d-none');
    }
    
    return isValid;
}

// CALCULATION FUNCTIONS
function calculateAll() {
    calculateAmountWithoutGST();
    calculateGST();
    calculateTransportGST();
    calculateLoadingGST();
    calculateTotals();
}

function cleanNumberInput(value) {
    if (!value || isNaN(value)) return 0;
    return parseFloat(value.toString().replace(/,/g, ''));
}

function calculateAmountWithoutGST() {
    const quantity = cleanNumberInput($('#quantity').val());
    const rate = cleanNumberInput($('#basic_rate').val());
    const amount = quantity * rate;
    $('#amount_without_gst').val(amount.toFixed(2)).trigger('change'); // Force UI update
}

function calculateGST() {
    const material = $('#material').val();
    const gstType = $('input[name="gst_type"]:checked').val();
    const amountWithoutGST = cleanNumberInput($('#amount_without_gst').val());
    
    let cgst = 0, sgst = 0, igst = 0;
    
    if (material && gstType && amountWithoutGST > 0) {
        if (gstType === 'Intra-State' && MATERIAL_RATES[material]) {
            cgst = (amountWithoutGST * MATERIAL_RATES[material].cgst) / 100;
            sgst = (amountWithoutGST * MATERIAL_RATES[material].sgst) / 100;
        } else if (gstType === 'Inter-State' && MATERIAL_RATES[material]) {
            igst = (amountWithoutGST * MATERIAL_RATES[material].igst) / 100;
        }
    }
    
    // Update values and force UI refresh
    $('#cgst').val(cgst.toFixed(2)).trigger('input');
    $('#sgst').val(sgst.toFixed(2)).trigger('input');
    $('#igst').val(igst.toFixed(2)).trigger('input');
    
    // Debugging - log the values to console
    console.log('GST Calculated:', {cgst, sgst, igst});
}

function calculateTransportGST() {
    const withGST = $('input[name="transport_with_gst"]:checked').val() === 'with';
    const transportAmount = cleanNumberInput($('#transport_amount').val());
    
    let transportCGST = 0, transportSGST = 0;
    
    if (withGST && transportAmount > 0) {
        transportCGST = (transportAmount * 2.5) / 100;
        transportSGST = (transportAmount * 2.5) / 100;
    }
    
    $('#transport_cgst').val(transportCGST.toFixed(2)).trigger('input');
    $('#transport_sgst').val(transportSGST.toFixed(2)).trigger('input');
    console.log('Transport GST Calculated:', {transportCGST, transportSGST});
}

function calculateLoadingGST() {
    const withGST = $('input[name="loading_with_gst"]:checked').val() === 'with';
    const loadingAmount = cleanNumberInput($('#loading_amount').val());
    
    let loadingCGST = 0, loadingSGST = 0;
    
    if (withGST && loadingAmount > 0) {
        loadingCGST = (loadingAmount * 9) / 100;
        loadingSGST = (loadingAmount * 9) / 100;
    }
    
    $('#loading_cgst').val(loadingCGST.toFixed(2)).trigger('input');
    $('#loading_sgst').val(loadingSGST.toFixed(2)).trigger('input');
    console.log('Loading GST Calculated:', {loadingCGST, loadingSGST});
}

function calculateTotals() {
    const amountWithoutGST = cleanNumberInput($('#amount_without_gst').val());
    const cgst = cleanNumberInput($('#cgst').val());
    const sgst = cleanNumberInput($('#sgst').val());
    const igst = cleanNumberInput($('#igst').val());
    const cess = cleanNumberInput($('#cess').val());
    const tcs = cleanNumberInput($('#tcs').val());
    
    const transportAmount = cleanNumberInput($('#transport_amount').val());
    const transportCGST = cleanNumberInput($('#transport_cgst').val());
    const transportSGST = cleanNumberInput($('#transport_sgst').val());
    const transportTDSamount = (transportAmount * (cleanNumberInput($('#transport_tds').val()) || 0)) / 100;
    const transportTDS = transportAmount - transportTDSamount;
    
    const loadingAmount = cleanNumberInput($('#loading_amount').val());
    const loadingCGST = cleanNumberInput($('#loading_cgst').val());
    const loadingSGST = cleanNumberInput($('#loading_sgst').val());
    const loadingTDSamount = (loadingAmount * (cleanNumberInput($('#loading_tds').val()) || 0)) / 100;
    const loadingTDS = loadingAmount - loadingTDSamount;

    const total_TDS_amount = transportTDSamount + loadingTDSamount;
    const totalCess = cess;
    const totalTcs = tcs;

    
    const totalGSTAmount = cgst + sgst + igst + 
                          transportCGST + transportSGST +  
                          loadingCGST + loadingSGST; 
    
    const totalExcludingGST = amountWithoutGST + transportAmount + loadingAmount;
    const totalIncludingGST = totalExcludingGST + totalGSTAmount;

    $('#transport_tds_amount').val(transportTDSamount.toFixed(2)).trigger('change');
    $('#transport_amount_after_tds').val(transportTDS.toFixed(2)).trigger('change');
    $('#transport_tds_amount').val(transportTDSamount.toFixed(2)).trigger('input');
    $('#transport_amount_after_tds').val(transportTDS.toFixed(2)).trigger('input');
    
    // Update loading TDS fields
    $('#loading_tds_amount').val(loadingTDSamount.toFixed(2)).trigger('change');
    $('#loading_amount_after_tds').val(loadingTDS.toFixed(2)).trigger('change');
    $('#loading_tds_amount').val(loadingTDSamount.toFixed(2)).trigger('input');
    $('#loading_amount_after_tds').val(loadingTDS.toFixed(2)).trigger('input');
    
    $('#total_TDS_amount').val(total_TDS_amount.toFixed(2)).trigger('change');
    $('#totalCess').val(totalCess.toFixed(2)).trigger('change');
    $('#totalTcs').val(totalTcs.toFixed(2)).trigger('change');
    $('#total_excluding_gst').val(totalExcludingGST.toFixed(2)).trigger('change');
    $('#total_gst_amount').val(totalGSTAmount.toFixed(2)).trigger('change');
    $('#total_including_gst').val(totalIncludingGST.toFixed(2)).trigger('change');
    $('#total_TDS_amount').val(total_TDS_amount.toFixed(2)).trigger('input');
    $('#totalCess').val(totalCess.toFixed(2)).trigger('input');
    $('#totalTcs').val(totalTcs.toFixed(2)).trigger('input');
    $('#total_excluding_gst').val(totalExcludingGST.toFixed(2)).trigger('input');
    $('#total_gst_amount').val(totalGSTAmount.toFixed(2)).trigger('input');
    $('#total_including_gst').val(totalIncludingGST.toFixed(2)).trigger('input');
    
    }

    // Initialize everything
    setupEventHandlers();
    calculateAll();
});