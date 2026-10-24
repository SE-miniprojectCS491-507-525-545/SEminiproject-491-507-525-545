# Requirements Traceability Matrix (RTM)

| Requirement ID | Summary | Related test cases | Coverage / status |
|---|---|---|---|
| FR-01 | Search trains | TC-SEARCH-001–005 | Implemented; automated tests passed |
| FR-02 | Check seat availability | TC-AVAIL-001–002 | Implemented; automated tests passed |
| FR-03 | Validate search inputs | TC-SEARCH-006–013 | Implemented; automated tests passed |
| FR-04 | Book ticket and generate PNR | TC-BOOK-001–002, 007–008 | Implemented; automated tests passed |
| FR-05 | Validate passenger details | TC-BOOK-003–004 | Implemented; automated tests passed |
| FR-06 | Cancel ticket | TC-CAN-001 | Implemented; automated tests passed |
| FR-07 | Calculate/display refund | TC-REF-001–003 | Implemented; refund preview tested; the confirmation step needs a screen |
| FR-08 | Validate cancellation PNR | TC-CAN-002–003 | Implemented; automated tests passed |
| BR-01 | Maximum six passengers per booking | TC-BOOK-005 | Implemented; automated tests passed |
| BR-02 | Cancellation deadline and refund rule | TC-CAN-004, TC-REF-003 | Implemented; automated tests passed; figures recorded in the deviation log |
| NFR-01 | Search response time ≤ 5 seconds | TC-SEARCH-014 | Not measured yet |
| NFR-02 | First-time search usability | TC-USE-001 | Planned; UI needs to be available |
| NFR-03 | Prevent duplicate seat assignment | TC-BOOK-006 | Implemented; automated tests passed, including two simultaneous bookings for the last seat |
| NFR-04 | Immediately update availability after cancellation | TC-DATA-001 | Implemented; automated tests passed |
| FR-09 | Passenger registration | TC-REG-001–003 | Implemented; automated tests passed |
| FR-10 | Passenger login and logout | TC-LOGIN-001–003 | Implemented; automated tests passed |
| FR-11 | View booking by PNR | TC-PNR-001–002 | Planned |
| FR-12 | View my bookings | TC-HIST-001–002 | Planned |
| FR-13 | Admin adds train | TC-ADM-001–002 | Planned |
| FR-14 | Admin updates or removes train | TC-ADM-003–004 | Planned |
| FR-15 | Admin views all bookings | TC-ADM-005–006 | Planned |
| NFR-05 | Data persistence | TC-DATA-002 | Implemented at the storage layer; automated test passed |
| SR-01 | Salted password hashing | TC-SEC-001 | Implemented; automated tests passed |
| SR-02 | Role-based and ownership access control | TC-SEC-002–003 | Planned |

## Coverage note

Automated tests now cover FR-01 to FR-10, BR-01, BR-02, NFR-03, NFR-04 and SR-01, plus the storage layer for NFR-05. Booking is tested at function level; there is no screen yet. Requirement traceability does not mean every requirement has been implemented or passed.
