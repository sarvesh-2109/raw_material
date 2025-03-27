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
        'Mortar Bags': {cgst: 0, sgst: 0, igst: 0}
    };

    // Set up event handlers for all input fields
    function setupEventHandlers() {
        // Quantity and Basic Rate
        $('#quantity, #basic_rate').on('input', function() {
            calculateAmountWithoutGST();
            calculateGST();
            calculateTotals();
        });

        // Material and GST Type
        $('#material').on('change', function() {
            calculateGST();
            calculateTotals();
        });
        
        $('input[name="gst_type"]').on('change', function() {
            calculateGST();
            calculateTotals();
        });

        // Transport Section
        $('#transport_amount').on('input', function() {
            calculateTransportGST();
            calculateTotals();
        });
        
        $('input[name="transport_with_gst"]').on('change', function() {
            calculateTransportGST();
            calculateTotals();
        });

        // Loading Section
        $('#loading_amount').on('input', function() {
            calculateLoadingGST();
            calculateTotals();
        });
        
        $('input[name="loading_with_gst"]').on('change', function() {
            calculateLoadingGST();
            calculateTotals();
        });

        // Other fields
        $('#cess, #tcs, #transport_tds, #loading_tds').on('input', calculateTotals);

        // Vehicle number uppercase
        $('#vehicle_number').on('input', function() {
            this.value = this.value.toUpperCase();
            validateVehicleNumber();
        });
    }

    // Form validation before submission
    $('#invoiceForm').on('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            // Scroll to first error
            $('html, body').animate({
                scrollTop: $('.is-invalid').first().offset().top - 100
            }, 500);
        }
    });

    // Initialize everything
    setupEventHandlers();
    calculateAll();
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
    $('#amount_without_gst').val(amount.toFixed(2));
}

function calculateGST() {
    const material = $('#material').val();
    const gstType = $('input[name="gst_type"]:checked').val();
    const amountWithoutGST = cleanNumberInput($('#amount_without_gst').val());
    
    let cgst = 0, sgst = 0, igst = 0;
    
    if (material && gstType && amountWithoutGST > 0) {
        const rates = {
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
            'Mortar Bags': {cgst: 0, sgst: 0, igst: 0}
        };
        
        if (gstType === 'Intra-State' && rates[material]) {
            cgst = (amountWithoutGST * rates[material].cgst) / 100;
            sgst = (amountWithoutGST * rates[material].sgst) / 100;
        } else if (gstType === 'Inter-State' && rates[material]) {
            igst = (amountWithoutGST * rates[material].igst) / 100;
        }
    }
    
    $('#cgst').val(cgst.toFixed(2));
    $('#sgst').val(sgst.toFixed(2));
    $('#igst').val(igst.toFixed(2));
}

function calculateTransportGST() {
    const withGST = $('input[name="transport_with_gst"]:checked').val() === 'with';
    const transportAmount = cleanNumberInput($('#transport_amount').val());
    
    let transportCGST = 0, transportSGST = 0;
    
    if (withGST && transportAmount > 0) {
        transportCGST = (transportAmount * 2.5) / 100;
        transportSGST = (transportAmount * 2.5) / 100;
    }
    
    $('#transport_cgst').val(transportCGST.toFixed(2));
    $('#transport_sgst').val(transportSGST.toFixed(2));
}

function calculateLoadingGST() {
    const withGST = $('input[name="loading_with_gst"]:checked').val() === 'with';
    const loadingAmount = cleanNumberInput($('#loading_amount').val());
    
    let loadingCGST = 0, loadingSGST = 0;
    
    if (withGST && loadingAmount > 0) {
        loadingCGST = (loadingAmount * 9) / 100;
        loadingSGST = (loadingAmount * 9) / 100;
    }
    
    $('#loading_cgst').val(loadingCGST.toFixed(2));
    $('#loading_sgst').val(loadingSGST.toFixed(2));
}

function calculateTotals() {
    const amountWithoutGST = cleanNumberInput($('#amount_without_gst').val());
    const cgst = cleanNumberInput($('#cgst').val());
    const sgst = cleanNumberInput($('#sgst').val());
    const igst = cleanNumberInput($('#igst').val());
    const cess = cleanNumberInput($('#cess').val());
    const tcs = cleanNumberInput($('#tcs').val()) || 0;
    
    const transportAmount = cleanNumberInput($('#transport_amount').val());
    const transportCGST = cleanNumberInput($('#transport_cgst').val());
    const transportSGST = cleanNumberInput($('#transport_sgst').val());
    const transportTDS = (transportAmount * (cleanNumberInput($('#transport_tds').val()) || 0)) / 100;
    
    const loadingAmount = cleanNumberInput($('#loading_amount').val());
    const loadingCGST = cleanNumberInput($('#loading_cgst').val());
    const loadingSGST = cleanNumberInput($('#loading_sgst').val());
    const loadingTDS = (loadingAmount * (cleanNumberInput($('#loading_tds').val()) || 0)) / 100;
    
    const totalGSTAmount = cgst + sgst + igst + cess + tcs + 
                          transportCGST + transportSGST + transportTDS + 
                          loadingCGST + loadingSGST + loadingTDS;
    
    const totalExcludingGST = amountWithoutGST + transportAmount + loadingAmount;
    const totalIncludingGST = totalExcludingGST + totalGSTAmount;
    
    $('#total_excluding_gst').val(totalExcludingGST.toFixed(2));
    $('#total_gst_amount').val(totalGSTAmount.toFixed(2));
    $('#total_including_gst').val(totalIncludingGST.toFixed(2));
}