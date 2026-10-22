# Railway Reservation System — Requirements

## 1. Functional Requirements

### FR-01 — Train Search

**Requirement:**
The system shall allow a passenger to search for available trains by providing the source station, destination station, and travel date.

**Priority:** High

**Acceptance Criteria:**

* The passenger can enter a source station.
* The passenger can enter a destination station.
* The passenger can enter a travel date.
* The system displays trains matching the provided search criteria.
* If no matching train is available, the system displays an appropriate message.

---

### FR-02 — Check Seat Availability

**Requirement:**
The system shall allow a passenger to view the number of available seats for each class on a selected train and travel date.

**Priority:** High

**Acceptance Criteria:**

* The passenger can select a train from the search results.
* The system displays available seats per class (e.g., Sleeper, 3AC, 2AC, 1AC).
* If no seats are available in a class, the system displays "Waiting list" or "Not available".
* Seat counts reflect the most recent bookings and cancellations.

---

### FR-03 — Search Input Validation

**Requirement:**
The system shall validate all train search inputs and reject invalid entries with a clear error message.

**Priority:** Medium

**Acceptance Criteria:**

* The system rejects a search where the source and destination stations are the same.
* The system rejects a station name that does not exist in the system.
* The system rejects a travel date in the past.
* The system rejects a search with any empty field and states which field is missing.

---

### FR-04 — Book Ticket

**Requirement:**
The system shall allow a registered passenger to book a ticket on a selected train, travel date and class by providing passenger details.

**Priority:** High

**Acceptance Criteria:**

* The passenger can book only if seats are available in the selected class.
* The passenger provides name, age and gender for each traveller.
* The system generates a unique PNR (booking reference) after a successful booking.
* The system reduces the available seat count for that class by the number of tickets booked.
* The system displays a booking confirmation with PNR, train, date, class and fare.

---

### FR-05 — Passenger Detail Validation

**Requirement:**
The system shall validate passenger details before confirming a booking.

**Priority:** Medium

**Acceptance Criteria:**

* The system rejects an empty passenger name.
* The system rejects an age that is not between 1 and 120.
* The system rejects a booking of more than 6 passengers in a single transaction.
* The system displays which field is invalid.

---

### FR-06 — Cancel Ticket

**Requirement:**
The system shall allow a passenger to cancel a booked ticket by entering the PNR.

**Priority:** High

**Acceptance Criteria:**

* The passenger can enter a PNR to look up a booking.
* The system cancels a valid, active booking and releases the seats back to availability (the available seat count for that class increases by the number of cancelled seats).
* The system displays an error for an invalid PNR.
* The system displays an error if the booking is already cancelled.
* The system displays a cancellation confirmation with the PNR and status.

---

### FR-07 — View Refund Amount

**Requirement:**
The system shall display the refund amount to the passenger before the cancellation is confirmed.

**Priority:** Medium

**Acceptance Criteria:**

* The refund amount is calculated from the ticket fare and the cancellation rule (BR-02).
* The system shows the refund amount and asks for confirmation before cancelling.
* The passenger can decline and keep the booking.

---

### FR-08 — Cancellation Input Validation

**Requirement:**
The system shall validate the PNR entered for cancellation and reject invalid entries with a clear error message.

**Priority:** Medium

**Acceptance Criteria:**

* The system rejects an empty PNR field.
* The system rejects a PNR that does not exist in the system.
* The system rejects cancellation of a booking that has already been cancelled.

## 2. Business Rules

### BR-01 — Maximum 6 Passengers

A single booking may contain at most 6 passengers.

---

### BR-02 — Cancellation and Refund Rules

A booking can be cancelled only up to 4 hours before the scheduled departure time (exactly 4 hours is allowed). A cancellation closer than 4 hours, including after departure, is refused, so no refund is paid in that case.

Otherwise the refund is the ticket fare minus a cancellation fee: **10%** of the fare when cancelling more than 24 hours before departure, and **50%** from 24 hours down to 4 hours before departure. The team may still change these figures (see `docs/deviation-log.md`).

## 3. Non-Functional Requirements

### NFR-01 — Performance

**Requirement:**
The system shall return train search results within **5 seconds** in normal usage.

**Priority:** High

**Acceptance Criteria:**

* A valid train search request should return results within 5 seconds under normal operating conditions.
* The system should display an appropriate response if the search cannot be completed.

---

### NFR-02 — Usability

**Requirement:**
A first-time passenger shall be able to complete a train search without external help.

**Priority:** Medium

**Acceptance Criteria:**

* The search form has no more than three required fields.
* Error messages state what is wrong and how to fix it.

---

### NFR-03 — Reliability

**Requirement:**
The system shall never assign the same seat to two different passengers for the same train, date and class.

**Priority:** High

**Acceptance Criteria:**

* Two simultaneous bookings for the last available seat result in exactly one confirmed booking.
* The second passenger receives a "No seats available" message.

---

### NFR-04 — Data Consistency

**Requirement:**
The system shall ensure that a cancelled seat is immediately available for a new booking.

**Priority:** High

**Acceptance Criteria:**

* Once a cancellation is confirmed, the seat count update is visible to the next search/booking request with no delay.

## 4. Requirements Defined in the SRS

The remaining requirements are specified in `docs/SRS.docx`: FR-09 (registration), FR-10 (login and logout), FR-11 (view booking by PNR), FR-12 (view my bookings), FR-13 to FR-15 (administration), NFR-05 (data persistence), SR-01 (password protection) and SR-02 (access control). This file and the SRS use the same IDs.
