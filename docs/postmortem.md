# Postmortem: Stale Frontend State Causing Phantom RSVP Cancellations

**Author:** Dhruv Puri
**Date:** 25 July 2026
**Incident Date:** 11 June 2026
**Severity:** Medium (data integrity risk, no data loss)
**Status:** Resolved

---

## Summary

After an admin submitted (locked) attendance for an event, students could still see a "Cancel RSVP" button in their dashboard. Clicking it sent a `DELETE /api/events/{id}/rsvp` request. The backend correctly rejected it with a 400 ("Attendance already finalized"), but the frontend showed a generic "Network Error" toast and left the button visible. In some cases, rapid clicking before the error response arrived caused the UI to enter an inconsistent state where the RSVP appeared cancelled locally but still existed in the database.

## Timeline

| Time | Event |
|:-----|:------|
| 10 Jun, ~14:00 | Implemented `submit-attendance` endpoint and `attendance_submitted` flag. Tested via Swagger UI — backend correctly blocks DELETE/PUT after locking. |
| 10 Jun, ~16:00 | Connected the attendance manager UI. Admin can lock attendance from the dashboard. Event disappears from student views. |
| 11 Jun, ~10:00 | During manual testing, noticed that if a student had the dashboard open *before* the admin locked attendance, the "Cancel RSVP" button remained visible. |
| 11 Jun, ~10:30 | Clicked "Cancel RSVP" after lock. Backend returned 400. Frontend showed "Network Error" (wrong — it was a 400, not a network error). Button still visible. |
| 11 Jun, ~11:00 | Rapid-clicked the button 5 times. UI showed the RSVP as cancelled (optimistic update) but a page refresh showed it still existed. **State desync confirmed.** |
| 11 Jun, ~14:00 | Root cause identified. Fix implemented. |
| 11 Jun, ~16:00 | Fix verified across all three roles. No regression. |

## Root Cause

Three compounding issues:

1. **No frontend state refresh after backend state change.** When the admin locked attendance, the student's browser had no way to know. The `state.rsvps` array in `dashboard.js` still contained the old RSVP object. The "Cancel RSVP" button was rendered based on stale local state, not the current backend truth.

2. **Incorrect error handling in `cancelRSVP()`.** The `catch` block showed "Network Error" for *all* failures, including 400 responses. The student saw "Network Error" and assumed a connectivity issue, not a business rule violation.

3. **No backend error message propagation.** The `cancelRSVP()` function didn't read `err.detail` from the 400 response body. The backend's clear message ("Cannot cancel RSVP. Attendance for this event has already been finalized.") was discarded.

## The Fix

**Backend (already correct):** The `DELETE /api/events/{id}/rsvp` endpoint checks `event.attendance_submitted` and `rsvp.attendance.is_present` before allowing deletion. Returns 400 with a descriptive `detail` message. No change needed.

**Frontend (three changes):**

```javascript
// 1. Read and display the actual backend error message
async function cancelRSVP(eventId) {
    try {
        const res = await authFetch(`/api/events/${eventId}/rsvp`, { method: 'DELETE' });
        if (res.ok) {
            showToast("RSVP Cancelled!", 'success');
        } else {
            const err = await res.json();
            showToast(err.detail || "Failed to cancel RSVP", 'error'); // ← Shows real reason
        }
    } catch (e) {
        showToast("Network Error", 'error');
    }
    // 2. ALWAYS re-fetch and re-render, regardless of success/failure
    await Promise.all([fetchEvents(), fetchMyRsvps(), fetchNotifications()]);
    renderDashboard();
}
