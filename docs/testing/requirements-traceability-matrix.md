# Requirements Traceability Matrix (RTM)

| Requirement ID | Summary | Related test cases | Coverage / status |
|---|---|---|---|
| FR-01 | Search trains | TC-SEARCH-001–005 | Implemented; automated tests passed |
| FR-02 | Check seat availability | TC-AVAIL-001–002 | Planned; feature not present in current baseline |
| FR-03 | Validate search inputs | TC-SEARCH-006–013 | Implemented; automated tests passed |
| FR-04 | Book ticket and generate PNR | TC-BOOK-001–002 | Planned; feature not present in current baseline |
| FR-05 | Validate passenger details | TC-BOOK-003–004 | Planned |
| FR-06 | Cancel ticket | TC-CAN-001 | Planned |
| FR-07 | Calculate/display refund | TC-REF-001–003 | Planned; exact refund slabs need confirmation |
| FR-08 | Validate cancellation PNR | TC-CAN-002–003 | Planned |
| BR-01 | Maximum six passengers per booking | TC-BOOK-005 | Planned |
| BR-02 | Cancellation deadline and refund rule | TC-CAN-004, TC-REF-003 | Planned; source requirements reuse BR-02 for two rules |
| NFR-01 | Search response time ≤ 5 seconds | TC-SEARCH-014 | Not measured yet |
| NFR-02 | First-time search usability | TC-USE-001 | Planned; UI needs to be available |
| NFR-03 | Prevent duplicate seat assignment | TC-BOOK-006 | Planned; booking/concurrency logic needs to be available |
| NFR-04 | Immediately update availability after cancellation | TC-DATA-001 | Planned |

## Coverage note

The current automated implementation verifies **FR-01** and **FR-03**. Requirement traceability does not mean every requirement has been implemented or passed. Remaining requirements are retained so testing can be completed when the corresponding features are integrated.
