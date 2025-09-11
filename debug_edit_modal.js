// Debug script to test edit modal functionality
// Paste this into browser console to debug modal issues

console.log('=== EDIT MODAL DEBUG SCRIPT ===');

// Check basic requirements
console.log('1. Bootstrap available:', typeof bootstrap !== 'undefined');
console.log('2. Bootstrap Modal available:', typeof bootstrap !== 'undefined' && typeof bootstrap.Modal !== 'undefined');

// Check DOM elements
const editModal = document.getElementById('editStatusModal');
console.log('3. Edit modal element exists:', !!editModal);

if (editModal) {
    console.log('4. Modal classes:', editModal.className);
    console.log('5. Modal style display:', editModal.style.display);
    console.log('6. Modal computed display:', window.getComputedStyle(editModal).display);
}

// Check form elements
const editForm = document.getElementById('editStatusForm');
console.log('7. Edit form exists:', !!editForm);

// Test modal manually
function testEditModal() {
    console.log('Testing modal manually...');
    
    if (!editModal) {
        console.error('Modal element not found!');
        return;
    }
    
    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap Modal not available!');
        return;
    }
    
    try {
        // Populate some test data
        document.getElementById('edit_status_date').value = '2025-09-12';
        document.getElementById('edit_status').value = 'in_office_full';
        document.getElementById('edit_location').value = 'BL-A-5F';
        document.getElementById('edit_comments').value = 'Test comment';
        
        // Create and show modal
        const modalInstance = new bootstrap.Modal(editModal);
        modalInstance.show();
        console.log('Modal show() called - it should be visible now');
        
        // Add event listeners to track modal events
        editModal.addEventListener('show.bs.modal', () => console.log('Modal show event fired'));
        editModal.addEventListener('shown.bs.modal', () => console.log('Modal shown event fired'));
        editModal.addEventListener('hide.bs.modal', () => console.log('Modal hide event fired'));
        editModal.addEventListener('hidden.bs.modal', () => console.log('Modal hidden event fired'));
        
    } catch (error) {
        console.error('Error testing modal:', error);
    }
}

// Test the editStatus function if it exists
function testEditStatusFunction() {
    console.log('Testing editStatus function...');
    
    if (typeof editStatus === 'function') {
        console.log('editStatus function exists, testing with mock data...');
        
        // Mock the fetch to avoid actual server call
        const originalFetch = window.fetch;
        window.fetch = function(url) {
            console.log('Mock fetch called for:', url);
            return Promise.resolve({
                json: () => Promise.resolve({
                    status_date: '2025-09-12',
                    status: 'in_office_full',
                    location: 'BL-A-5F',
                    comments: 'Test comment',
                    approval_status: 'pending'
                })
            });
        };
        
        editStatus(123);
        
        // Restore original fetch after a delay
        setTimeout(() => {
            window.fetch = originalFetch;
        }, 1000);
        
    } else {
        console.error('editStatus function not found!');
    }
}

// Provide test functions globally
window.testEditModal = testEditModal;
window.testEditStatusFunction = testEditStatusFunction;

console.log('Debug script loaded. Available functions:');
console.log('- testEditModal(): Test modal display manually');
console.log('- testEditStatusFunction(): Test editStatus function with mock data');
console.log('=== END DEBUG SCRIPT ===');
