/**
 * Enhanced Dynamic Form Behavior for Daily Status Submission
 * Adds smoother transitions, better feedback, and improved UX
 */

// Safety wrapper functions to prevent errors when DOM elements don't exist
function safeGetElement(id) {
    return document.getElementById(id);
}

function safeSetValue(id, value) {
    const element = safeGetElement(id);
    if (element) element.value = value;
}

function safeSetTextContent(id, content) {
    const element = safeGetElement(id);
    if (element) element.textContent = content;
}

// Use original page functions directly (no wrappers) to avoid recursion
// - setDefaultFullDayTimes(status)
// - updateHalfDayTimeTracking(amType, pmType)
// - updateLocationForHalfDay(amType, pmType)

// Enhanced status change handler with animations
function enhancedHandleStatusChange() {
    const statusEl = safeGetElement('status');
    if (!statusEl) return;
    
    const status = statusEl.value;
    const timeTrackingSection = safeGetElement('timeTrackingSection');
    const fullDayTiming = safeGetElement('fullDayTiming');
    const halfDayTiming = safeGetElement('halfDayTiming');
    const halfDayComboSection = safeGetElement('halfDayComboSection');
    const officeHalf = safeGetElement('officeHalf');
    const wfhHalf = safeGetElement('wfhHalf');
    
    // Add smooth transition classes
    const transitionClass = 'form-section-transition';
    [timeTrackingSection, fullDayTiming, halfDayTiming, halfDayComboSection, officeHalf, wfhHalf].forEach(el => {
        if (el) el.classList.add(transitionClass);
    });
    
    // Show loading feedback
    showStatusChangeLoading(true);
    
    setTimeout(() => {
        // Hide all sections first with fade out
        hideAllSectionsSmooth();
        
        // Clear all fields safely
        if (typeof clearAllTimeFields === 'function') {
            clearAllTimeFields();
        }
        if (typeof clearHalfDaySelection === 'function') {
            clearHalfDaySelection();
        }
        
        // Show relevant sections based on status
        if (status === 'in_office_full' || status === 'wfh_full') {
            showSectionSmooth(timeTrackingSection);
            showSectionSmooth(fullDayTiming);
            // Call the original function if present; otherwise, fallback default
            if (typeof window.setDefaultFullDayTimes === 'function') {
                window.setDefaultFullDayTimes(status);
            } else {
                safeSetValue('in_time', '09:00');
                safeSetValue('out_time', '18:00');
            }
            updateLocationWithAnimation(status);
            
        } else if (status === 'in_office_half' || status === 'wfh_half' || status === 'leave_half') {
            showSectionSmooth(halfDayComboSection);
            
            // Pre-populate with logical defaults
            if (status === 'wfh_half') {
                setHalfDayDefaults('wfh', 'wfh');
            } else if (status === 'leave_half') {
                setHalfDayDefaults('leave', 'leave');
            } else if (status === 'in_office_half') {
                setHalfDayDefaults('in_office', 'wfh'); // Common pattern
            }
            
            // Use enhanced validation if available, otherwise fallback to original
            if (typeof enhancedValidateHalfDaySelection === 'function') {
                enhancedValidateHalfDaySelection();
            } else if (typeof validateHalfDaySelection === 'function') {
                validateHalfDaySelection();
            }
            // Ensure time tracking updates after selection
            if (typeof window.updateHalfDayTimeTracking === 'function') {
                const amSel = safeGetElement('half_am_type');
                const pmSel = safeGetElement('half_pm_type');
                if (amSel && pmSel) {
                    window.updateHalfDayTimeTracking(amSel.value, pmSel.value);
                }
            }
            
        } else if (status === 'leave_full' || status === 'absent') {
            updateLocationWithAnimation('');
        }
        
        // Add helpful hints
        showStatusHint(status);
        
        showStatusChangeLoading(false);
    }, 200);
}

function hideAllSectionsSmooth() {
    const sections = [
        'timeTrackingSection', 
        'fullDayTiming', 
        'halfDayTiming', 
        'halfDayComboSection', 
        'officeHalf', 
        'wfhHalf'
    ];
    
    sections.forEach(sectionId => {
        const element = safeGetElement(sectionId);
        if (element) {
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.display = 'none';
            }, 150);
        }
    });
}

function showSectionSmooth(element) {
    if (element) {
        element.style.display = 'block';
        element.style.opacity = '0';
        setTimeout(() => {
            element.style.opacity = '1';
        }, 50);
    }
}

function updateLocationWithAnimation(status) {
    const locationField = safeGetElement('location');
    if (!locationField) return;
    
    // Fade out current value
    locationField.style.opacity = '0.5';
    
    setTimeout(() => {
        if (status === 'wfh_full') {
            locationField.value = '🏠 Home';
        } else if (status === 'in_office_full') {
            locationField.value = '🏢 BL-A-5F';
        } else if (status === '') {
            locationField.value = '';
        }
        
        // Fade back in
        locationField.style.opacity = '1';
        
        // Add subtle highlight
        locationField.classList.add('field-updated');
        setTimeout(() => {
            locationField.classList.remove('field-updated');
        }, 1000);
    }, 150);
}

function setHalfDayDefaults(amType, pmType) {
    const amSelect = safeGetElement('half_am_type');
    const pmSelect = safeGetElement('half_pm_type');
    
    if (amSelect && pmSelect) {
        // Animate the selection
        [amSelect, pmSelect].forEach(select => {
            select.style.transform = 'scale(1.05)';
            setTimeout(() => {
                select.style.transform = 'scale(1)';
            }, 200);
        });
        
        amSelect.value = amType;
        pmSelect.value = pmType;
    }
}

function showStatusHint(status) {
    // Remove existing hints
    const existingHint = document.querySelector('.status-hint');
    if (existingHint) {
        existingHint.remove();
    }
    
    let hintText = '';
    let hintType = 'info';
    
    switch(status) {
        case 'in_office_full':
            hintText = '💼 Full day in office - Don\'t forget to swipe in/out!';
            break;
        case 'wfh_full':
            hintText = '🏠 Working from home - Ensure you\'re available during core hours';
            break;
        case 'in_office_half':
            hintText = '⚡ Half day mixing office and other activities';
            break;
        case 'leave_full':
            hintText = '🌴 Full day leave - Make sure you have approval';
            hintType = 'warning';
            break;
        case 'absent':
            hintText = '⚠️ Marking as absent - Consider if this should be leave instead';
            hintType = 'danger';
            break;
    }
    
    if (hintText) {
        const statusSelect = safeGetElement('status');
        if (!statusSelect) return;
        
        const hint = document.createElement('div');
        hint.className = `alert alert-${hintType} alert-dismissible status-hint mt-2`;
        hint.innerHTML = `
            <small>
                <i class="fas fa-lightbulb me-1"></i>
                ${hintText}
                <button type="button" class="btn-close btn-sm" onclick="this.parentElement.parentElement.remove()"></button>
            </small>
        `;
        
        statusSelect.parentElement.appendChild(hint);
        
        // Auto-remove hint after 8 seconds
        setTimeout(() => {
            if (hint.parentElement) {
                hint.remove();
            }
        }, 8000);
    }
}

function showStatusChangeLoading(show) {
    const statusSelect = safeGetElement('status');
    if (!statusSelect) return;
    
    if (show) {
        statusSelect.style.position = 'relative';
        
        const spinner = document.createElement('div');
        spinner.className = 'status-loading-spinner';
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin text-primary"></i>';
        spinner.style.cssText = `
            position: absolute;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            pointer-events: none;
            z-index: 10;
        `;
        
        statusSelect.parentElement.appendChild(spinner);
    } else {
        const spinner = document.querySelector('.status-loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Enhanced validation with better feedback
function enhancedValidateHalfDaySelection() {
    const amTypeEl = safeGetElement('half_am_type');
    const pmTypeEl = safeGetElement('half_pm_type');
    const validation = safeGetElement('halfDayValidation');
    const validationMessage = safeGetElement('halfDayValidationMessage');
    
    if (!amTypeEl || !pmTypeEl || !validation || !validationMessage) {
        return false;
    }
    
    const amType = amTypeEl.value;
    const pmType = pmTypeEl.value;
    
    // Hide validation by default
    validation.style.display = 'none';
    
    if (!amType || !pmType) {
        return false;
    }
    
    // Enhanced validation logic
    const invalidCombinations = [
        {
            condition: amType === 'absent' && pmType === 'absent',
            message: 'Both AM and PM cannot be absent. Use "Absent" as main status instead.',
            suggestion: 'Consider using "Absent" for the full day.'
        },
        {
            condition: amType === 'leave' && pmType === 'leave', 
            message: 'Both periods marked as leave. Use "On Leave - Full Day" instead.',
            suggestion: 'Switch to full day leave status.'
        },
        {
            condition: amType === 'wfh' && pmType === 'wfh',
            message: 'Both periods are WFH. Use "Work From Home - Full Day" instead.',
            suggestion: 'Switch to full day WFH status.'
        },
        {
            condition: amType === 'in_office' && pmType === 'in_office',
            message: 'Both periods in office. Use "In Office - Full Day" instead.',
            suggestion: 'Switch to full day office status.'
        }
    ];
    
    const invalid = invalidCombinations.find(combo => combo.condition);
    
    if (invalid) {
        validationMessage.innerHTML = `
            <div><strong>⚠️ ${invalid.message}</strong></div>
            <small class="text-muted mt-1 d-block">💡 ${invalid.suggestion}</small>
        `;
        validation.style.display = 'block';
        
        // Add shake animation to validation
        validation.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            validation.style.animation = '';
        }, 500);
        
        return false;
    }
    
    // Success feedback
    showValidationSuccess();
    updateHalfDayTimeTracking(amType, pmType);
    updateLocationForHalfDay(amType, pmType);
    
    return true;
}

function showValidationSuccess() {
    const validation = safeGetElement('halfDayValidation');
    const validationMessage = safeGetElement('halfDayValidationMessage');
    
    if (!validation || !validationMessage) {
        return;
    }
    
    // Temporarily show success message
    validation.className = 'alert alert-success mt-3';
    validationMessage.innerHTML = '<i class="fas fa-check-circle me-2"></i>Valid half-day combination selected!';
    validation.style.display = 'block';
    
    // Hide success message after 2 seconds
    setTimeout(() => {
        validation.style.display = 'none';
        validation.className = 'alert alert-danger mt-3'; // Reset to danger class
    }, 2000);
}

// Add CSS for smooth transitions
const style = document.createElement('style');
style.textContent = `
    .form-section-transition {
        transition: opacity 0.3s ease-in-out, transform 0.2s ease-in-out;
    }
    
    .field-updated {
        background-color: #d4edda !important;
        border-color: #28a745 !important;
        transition: all 0.3s ease;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .status-hint {
        animation: slideDown 0.3s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Replace the original functions if this enhanced version is loaded
if (typeof handleStatusChange === 'function') {
    window.originalHandleStatusChange = handleStatusChange;
    window.handleStatusChange = enhancedHandleStatusChange;
}

if (typeof validateHalfDaySelection === 'function') {
    window.originalValidateHalfDaySelection = validateHalfDaySelection;
    window.validateHalfDaySelection = enhancedValidateHalfDaySelection;
}
