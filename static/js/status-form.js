// Status form UX/logic (compatible with existing backend fields)
// - Supports full day, mixed half-day, wfh half, leave half, leave full, absent
// - Single shared Total Hours summary, consistent DOM ids

(function() {
  function $(id) { return document.getElementById(id); }
  function show(el) { if (el) el.style.display = 'block'; }
  function hide(el) { if (el) el.style.display = 'none'; }
  function setVal(id, val) { const el = $(id); if (el) el.value = val; }
  function getVal(id) { const el = $(id); return el ? el.value : ''; }

  function clearTimes() {
    ['in_time','out_time','office_in_time','office_out_time','wfh_in_time','wfh_out_time'].forEach(id => setVal(id, ''));
    const br = $('break_duration'); if (br) br.value = '';
    const total = $('totalHoursDisplay'); if (total) total.textContent = '0.0';
  }

  function minutesBetween(a,b){
    if(!a||!b) return 0;
    const [ah,am]=a.split(':').map(Number); const [bh,bm]=b.split(':').map(Number);
    const s=ah*60+am; let e=bh*60+bm; if(e<s) e+=24*60; return Math.max(0,e-s);
  }

  function calcTotal() {
    const status = getVal('status');
    let minutes = 0;
    const breakMin = parseInt(getVal('break_duration') || '0', 10) || 0;
    if (status.includes('full')) {
      minutes = minutesBetween(getVal('in_time'), getVal('out_time')) - breakMin;
    } else if (status.includes('half')) {
      minutes += minutesBetween(getVal('office_in_time'), getVal('office_out_time'));
      minutes += minutesBetween(getVal('wfh_in_time'), getVal('wfh_out_time'));
      minutes -= breakMin;
    }
    const hours = Math.max(0, minutes/60);
    const disp = $('totalHoursDisplay'); if (disp) disp.textContent = hours.toFixed(1);
    // ensure hidden input
    let h = document.querySelector('#statusForm input[name="total_hours"]');
    if (!h) { h = document.createElement('input'); h.type='hidden'; h.name='total_hours'; $('statusForm').appendChild(h); }
    h.value = hours.toFixed(2);
  }

  function setDefaultsForFull(status) {
    // use sensible defaults; do not touch when fields already filled by user
    if (!getVal('in_time')) setVal('in_time', '09:00');
    if (!getVal('out_time')) setVal('out_time', '18:00');
    calcTotal();
  }

  function setDefaultsForHalf(amType, pmType) {
    // Reset first, then set according to AM/PM types
    clearTimes();
    if (amType === 'in_office') { setVal('office_in_time','09:00'); setVal('office_out_time','13:00'); }
    if (amType === 'wfh')      { setVal('wfh_in_time','09:00');    setVal('wfh_out_time','13:00'); }
    if (pmType === 'in_office') { setVal('office_in_time','14:00'); setVal('office_out_time','18:00'); }
    if (pmType === 'wfh')      { setVal('wfh_in_time','14:00');    setVal('wfh_out_time','18:00'); }
    calcTotal();
  }

  function updateLocationFor(status, amType, pmType) {
    const loc = $('location'); if (!loc) return;
    if (status === 'wfh_full') loc.value = 'Home';
    else if (status === 'in_office_full') loc.value = 'BL-A-5F';
    else if (status === 'leave_full' || status === 'absent') loc.value = '';
    else if (status.includes('half')) {
      if ((amType==='in_office') || (pmType==='in_office')) {
        if ((amType==='wfh') || (pmType==='wfh')) loc.value = amType==='in_office' ? 'BL-A-5F / Home' : 'Home / BL-A-5F';
        else loc.value = 'BL-A-5F';
      } else if ((amType==='wfh') || (pmType==='wfh')) loc.value = 'Home';
      else loc.value = '';
    }
  }

  function validateHalfCombo() {
    const am = getVal('half_am_type');
    const pm = getVal('half_pm_type');
    const v = $('halfDayValidation'); const m = $('halfDayValidationMessage');
    if (!am || !pm) { if (v) v.style.display='none'; return false; }
    let msg = '';
    if (am==='absent' && pm==='absent') msg = 'Both AM and PM cannot be absent. Use "Absent" status instead.';
    else if (am==='leave' && pm==='leave') msg = 'Both are Leave. Use "On Leave - Full Day" instead.';
    else if (am==='wfh' && pm==='wfh') msg = 'Both are WFH. Use "Work From Home - Full Day" instead.';
    else if (am==='in_office' && pm==='in_office') msg = 'Both are In Office. Use "In Office - Full Day" instead.';

    if (msg) { if (m) m.textContent = msg; if (v) v.style.display='block'; return false; }
    if (v) v.style.display='none';
    // Reveal relevant timing sections
    const needsTime = (am==='in_office'||am==='wfh'||pm==='in_office'||pm==='wfh');
    show($('timeTrackingSection'));
    show($('timeSummaryRow'));
    if (needsTime) { show($('halfDayTiming')); }
    $('officeHalf').style.display = (am==='in_office'||pm==='in_office') ? 'block' : 'none';
    $('wfhHalf').style.display    = (am==='wfh'     ||pm==='wfh')      ? 'block' : 'none';
    setDefaultsForHalf(am, pm);
    updateLocationFor('half', am, pm);
    return true;
  }

  function onStatusChange() {
    const status = getVal('status');
    // Hide all
    hide($('timeTrackingSection')); hide($('fullDayTiming')); hide($('halfDayTiming')); hide($('timeSummaryRow'));
    hide($('halfDayComboSection')); hide($('officeHalf')); hide($('wfhHalf'));
    clearTimes();

    if (status === 'in_office_full' || status === 'wfh_full') {
      show($('timeTrackingSection')); show($('fullDayTiming')); show($('timeSummaryRow'));
      setDefaultsForFull(status);
      updateLocationFor(status);
    } else if (status === 'in_office_half' || status === 'wfh_half' || status === 'leave_half') {
      show($('halfDayComboSection'));
      // sensible suggestions
      if (status==='in_office_half') { setVal('half_am_type','in_office'); setVal('half_pm_type','wfh'); }
      else if (status==='wfh_half')  { setVal('half_am_type','wfh'); setVal('half_pm_type',''); }
      else if (status==='leave_half'){ setVal('half_am_type','leave'); setVal('half_pm_type',''); }
      // run validation when user is ready; do not show timers until combination valid
      validateHalfCombo();
    } else if (status === 'leave_full' || status === 'absent') {
      setVal('location','');
    }
  }

  function hookEvents() {
    const statusSel = $('status'); if (statusSel) statusSel.addEventListener('change', onStatusChange);
    ['in_time','out_time','office_in_time','office_out_time','wfh_in_time','wfh_out_time','break_duration']
      .forEach(id => { const el = $(id); if (el) el.addEventListener('change', calcTotal); });
    const am = $('half_am_type'); const pm = $('half_pm_type');
    if (am) am.addEventListener('change', validateHalfCombo);
    if (pm) pm.addEventListener('change', validateHalfCombo);

    // Form submit validation
    const form = $('statusForm');
    if (form) form.addEventListener('submit', function(e){
      const s = getVal('status');
      if (s==='in_office_half' || s==='wfh_half' || s==='leave_half') {
        if (!validateHalfCombo()) { e.preventDefault(); return false; }
      }
      calcTotal();
      return true;
    });
  }

  window.initStatusForm = function() {
    hookEvents();
    // initial state
    onStatusChange();
  };
})();
