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
```
```javascript
// 3. Disable Edit/Delete buttons when attendance_submitted is true (admin view)
const isLocked = e.attendance_submitted;
`<button class="btn btn-sm btn-danger" onclick="deleteEvent(${e.id})" 
    ${isLocked ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}>
    <i class="fas ${isLocked ? 'fa-lock' : 'fa-trash'}"></i> ${isLocked ? 'Locked' : 'Delete'}
</button>`
```

## Lessons Learned

1. **The frontend is a cache of backend state.** Any time the backend state changes (admin locks attendance, coordinator deletes a club), the frontend must re-fetch. Optimistic UI updates are dangerous without a reconciliation step. The "always re-fetch after mutation" pattern (`await Promise.all([fetchEvents(), fetchMyRsvps()]); renderDashboard();`) is now applied to every mutating action in `dashboard.js`.

2. **Error messages are a UX feature.** "Network Error" for a 400 response is actively misleading. Every `catch` block now reads `err.detail` and displays the backend's actual message. This took 10 minutes to implement and would have saved hours of user confusion.

3. **Test the multi-user scenario.** I tested the attendance lock in isolation (admin locks → verify backend rejects). I didn't test the *concurrent* scenario (student has dashboard open → admin locks → student clicks cancel). Multi-user state desync is a category of bug that only appears when you test with two browser windows.

4. **Backend guardrails are necessary but not sufficient.** The backend correctly rejected the invalid request. But the frontend allowed the user to *attempt* it, creating a confusing experience. Defence in depth means the UI should also prevent the action (disabled button + lock icon), not just the API.

## Prevention

- Every mutating frontend action now follows the pattern: `try → show success/error → ALWAYS re-fetch → re-render`.
- Admin-facing buttons (Edit, Delete, Mark Attendance) are disabled with a lock icon when `attendance_submitted === true`.
- The `cancelRSVP` function refreshes any open overlay (My RSVPs, Event Details) seamlessly without a full page reload.
