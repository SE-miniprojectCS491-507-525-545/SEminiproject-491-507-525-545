"""Streamlit UI for the Railway Reservation System.

Run with: PYTHONPATH=src streamlit run app.py
"""
from datetime import date, datetime
import streamlit as st
from railway import storage
from railway.access import require_admin
from railway.auth import current_passenger, login, logout
from railway.availability import list_availability
from railway.booking import book_ticket
from railway.booking_views import view_booking
from railway.cancellation import cancel_booking, calculate_refund, validate_deadline
from railway.demo_data import seed_demo_data
from railway.models import ROLE_ADMIN, SeatClass, Train, Traveller
from railway.registration import register_passenger
from railway.search import search_trains, stations_of

st.set_page_config(page_title="Railway Reservation System", page_icon="🚆", layout="wide")
st.title("🚆 Railway Reservation System")
st.caption("Search trains, book tickets and manage your journeys.")

def connection():
    if "db" not in st.session_state:
        st.session_state.db = storage.connect()
    return st.session_state.db

def passenger_now(conn):
    token = st.session_state.get("token")
    if not token:
        return None
    try:
        return current_passenger(token, storage.load_passengers(conn), st.session_state.sessions)
    except ValueError:
        st.session_state.pop("token", None)
        return None

def error(exc):
    st.error(str(exc))

def register(conn):
    st.subheader("Create an account")
    with st.form("register"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password", help="At least 8 characters, including a letter and a number.")
        confirm = st.text_input("Confirm password", type="password")
        submit = st.form_submit_button("Register", type="primary")
    if submit:
        if password != confirm:
            st.error("Passwords do not match.")
            return
        try:
            user = register_passenger(name, email, password, storage.load_passengers(conn))
            storage.add_passenger(conn, user)
            st.success("Account created. You can now log in.")
        except ValueError as exc:
            error(exc)

def login_screen(conn):
    st.subheader("Log in")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log in", type="primary")
    if submit:
        try:
            st.session_state.token = login(email, password, storage.load_passengers(conn), st.session_state.sessions)
            st.rerun()
        except ValueError as exc:
            error(exc)

def search_screen(conn):
    st.subheader("Search trains")
    trains = storage.list_trains(conn)
    stations = stations_of(trains)
    if not trains:
        st.info("No trains are available. Load demo data from the sidebar or ask an administrator to add trains.")
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        src = st.selectbox("From", stations)
    dests = [s for s in stations if s.lower() != src.lower()]
    with c2:
        dst = st.selectbox("To", dests) if dests else None
    with c3:
        day = st.date_input("Travel date", value=date.today(), min_value=date.today())
    if st.button("Search", type="primary", disabled=dst is None):
        try:
            found = search_trains(src, dst, day, trains, stations)
            if not found:
                st.warning("No trains found for this route and date.")
            for train in found:
                with st.container(border=True):
                    st.markdown(f"**{train.number} · {train.name}**")
                    st.write(f"{train.source} → {train.destination} · Departure {train.departure}")
                    for info in list_availability(conn, train.number, day):
                        st.write(f"{info.seat_class}: {info.free_seats}/{info.total_seats} seats · ₹{info.fare:,.2f}")
        except ValueError as exc:
            error(exc)

def availability_screen(conn):
    st.subheader("Seat availability")
    trains = storage.list_trains(conn)
    if not trains:
        st.info("No trains are available.")
        return
    choices = {f"{t.number} - {t.name}": t for t in trains}
    selected = st.selectbox("Train", list(choices), key="availability_train")
    day = st.date_input("Travel date", value=date.today(), min_value=date.today(), key="availability_day")
    if st.button("Check availability"):
        try:
            data = list_availability(conn, choices[selected].number, day)
            st.dataframe([{"Class": x.seat_class, "Total": x.total_seats, "Available": x.free_seats, "Fare": f"₹{x.fare:,.2f}", "Status": x.status} for x in data], use_container_width=True, hide_index=True)
        except ValueError as exc:
            error(exc)

def booking_screen(conn, user):
    st.subheader("Book a ticket")
    trains = storage.list_trains(conn)
    if not trains:
        st.info("No trains are available.")
        return
    choices = {f"{t.number} - {t.name} ({t.source} to {t.destination})": t for t in trains}
    with st.form("booking_form"):
        selected = st.selectbox("Train", list(choices))
        train = choices[selected]
        day = st.date_input("Travel date", value=date.today(), min_value=date.today())
        classes = [x.seat_class for x in storage.get_seat_classes(conn, train.number)]
        seat_class = st.selectbox("Class", classes)
        count = int(st.number_input("Number of passengers", min_value=1, max_value=6, value=1))
        people = []
        for i in range(count):
            st.markdown(f"**Passenger {i + 1}**")
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                nm = st.text_input("Name", key=f"person_name_{i}")
            with c2:
                age = st.number_input("Age", min_value=1, max_value=120, value=18, key=f"person_age_{i}")
            with c3:
                gender = st.selectbox("Gender", ["M", "F", "O"], key=f"person_gender_{i}")
            people.append(Traveller(nm, int(age), gender))
        submit = st.form_submit_button("Confirm booking", type="primary")
    if submit:
        try:
            ticket = book_ticket(conn, user.email, train.number, day, seat_class, people)
            st.success("Booking confirmed!")
            st.header(f"PNR: {ticket.pnr}")
            st.write(f"Train: {ticket.train_number} - {ticket.train_name}")
            st.write(f"Date: {ticket.travel_date} · Class: {ticket.seat_class}")
            st.write("Seats: " + ", ".join(map(str, ticket.seat_numbers)))
            st.metric("Total fare", f"₹{ticket.fare:,.2f}")
        except ValueError as exc:
            error(exc)

def bookings_screen(conn, user):
    st.subheader("My bookings")
    records = storage.list_bookings(conn, user.email)
    if not records:
        st.info("You have no bookings yet.")
        return
    for b in records:
        with st.container(border=True):
            train = storage.get_train(conn, b.train_number)
            st.markdown(f"**PNR {b.pnr}** · {b.status}")
            st.write(f"{b.train_number} - {train.name if train else ''} · {b.travel_date}")
            st.write(f"{b.seat_class} · {b.passengers} passenger(s) · ₹{b.fare:,.2f}")
            seats = storage.get_seat_numbers(conn, b.pnr)
            st.caption("Seats: " + (", ".join(map(str, seats)) if seats else "—"))

def pnr_screen(conn, user):
    st.subheader("Find booking by PNR")
    pnr = st.text_input("PNR")
    if st.button("View booking"):
        try:
            details = view_booking(conn, pnr, user)
            b = details.booking
            st.success(f"Status: {b.status}")
            st.write(f"Train: {b.train_number} - {details.train_name}")
            st.write(f"Date: {b.travel_date} · Class: {b.seat_class}")
            st.write("Passengers:")
            for person in details.travellers:
                st.write(f"- {person.name}, {person.age}, {person.gender}")
            st.write("Seats: " + (", ".join(map(str, details.seat_numbers)) or "Not allocated"))
            st.metric("Fare", f"₹{b.fare:,.2f}")
        except ValueError as exc:
            error(exc)

def cancel_screen(conn, user):
    st.subheader("Cancel booking")
    pnr = st.text_input("Booking PNR", key="cancel_pnr")
    if st.button("Calculate refund"):
        try:
            b = storage.get_booking(conn, pnr.strip())
            if b is None or (b.passenger_email.lower() != user.email.lower() and user.role != ROLE_ADMIN):
                raise ValueError(f"No booking found for PNR {pnr.strip()}.")
            if b.status != "CONFIRMED":
                raise ValueError("This booking is already cancelled.")
            train = storage.get_train(conn, b.train_number)
            if train is None:
                raise ValueError("The associated train could not be found.")
            departure = b.departure_at_booking or train.departure
            validate_deadline(b.travel_date, departure)
            refund = calculate_refund(b.fare, b.travel_date, departure)
            st.session_state.cancel_pending = {"pnr": b.pnr, "refund": refund}
        except ValueError as exc:
            st.session_state.pop("cancel_pending", None)
            error(exc)
    pending = st.session_state.get("cancel_pending")
    if pending:
        st.info(f"Estimated refund: ₹{pending['refund']:,.2f}")
        if st.button("Confirm cancellation", type="primary"):
            try:
                result = cancel_booking(conn, pending["pnr"])
                st.success(f"Cancelled {result.pnr}. Released {result.seats_released} seat(s). Refund: ₹{result.refund_amount:,.2f}")
                st.session_state.pop("cancel_pending", None)
            except ValueError as exc:
                error(exc)

def admin_screen(conn, user):
    st.subheader("Train administration")
    try:
        require_admin(user)
    except ValueError as exc:
        error(exc)
        return
    add_tab, edit_tab, remove_tab = st.tabs(["Add train", "Update train", "Remove train"])
    with add_tab:
        with st.form("add_train"):
            number = st.text_input("Train number")
            name = st.text_input("Train name")
            source = st.text_input("Source")
            destination = st.text_input("Destination")
            departure = st.text_input("Departure (HH:MM)", "08:30")
            days = st.multiselect("Operating days", list(range(7)), default=list(range(7)), format_func=lambda n: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][n])
            seat_class = st.text_input("Initial class", "SL")
            seats = st.number_input("Total seats", min_value=1, value=50)
            fare = st.number_input("Fare (₹)", min_value=0.0, value=500.0)
            submit = st.form_submit_button("Add train")
        if submit:
            try:
                if not all(x.strip() for x in (number, name, source, destination, seat_class)):
                    raise ValueError("All train fields are required.")
                if source.strip().casefold() == destination.strip().casefold():
                    raise ValueError("Source and destination must differ.")
                datetime.strptime(departure, "%H:%M")
                if not days:
                    raise ValueError("Select at least one operating day.")
                train = Train(number.strip(), name.strip(), source.strip(), destination.strip(), departure, tuple(sorted(days)))
                storage.add_train(conn, train, [SeatClass(number.strip(), seat_class.strip().upper(), int(seats), float(fare))])
                st.success("Train added successfully.")
            except (ValueError, TypeError) as exc:
                error(exc)
    trains = storage.list_trains(conn)
    choices = {f"{t.number} - {t.name}": t for t in trains}
    with edit_tab:
        if choices:
            selected = st.selectbox("Train to update", list(choices), key="edit_train")
            old = choices[selected]
            with st.form("update_train"):
                name = st.text_input("Train name", old.name)
                source = st.text_input("Source", old.source)
                destination = st.text_input("Destination", old.destination)
                departure = st.text_input("Departure (HH:MM)", old.departure)
                days = st.multiselect("Operating days", list(range(7)), default=list(old.runs_on), format_func=lambda n: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][n])
                submit = st.form_submit_button("Save changes")
            if submit:
                try:
                    datetime.strptime(departure, "%H:%M")
                    if not all(x.strip() for x in (name, source, destination)) or source.strip().casefold() == destination.strip().casefold() or not days:
                        raise ValueError("Enter valid train details and operating days.")
                    storage.update_train(conn, Train(old.number, name.strip(), source.strip(), destination.strip(), departure, tuple(sorted(days))))
                    st.success("Train updated.")
                except (ValueError, TypeError) as exc:
                    error(exc)
        else:
            st.info("No trains to update.")
    with remove_tab:
        if choices:
            selected = st.selectbox("Train to remove", list(choices), key="remove_train")
            confirm = st.checkbox("Confirm train deactivation")
            if st.button("Remove train", disabled=not confirm):
                try:
                    storage.remove_train(conn, choices[selected].number)
                    st.success("Train deactivated.")
                    st.rerun()
                except ValueError as exc:
                    error(exc)
        else:
            st.info("No trains to remove.")

def main():
    conn = connection()
    st.session_state.setdefault("sessions", {})
    user = passenger_now(conn)
    with st.sidebar:
        st.header("Menu")
        if user:
            st.success(f"Logged in: {user.name}")
            pages = ["Search trains", "Seat availability", "Book ticket", "My bookings", "Find booking by PNR", "Cancel booking"]
            if user.role == ROLE_ADMIN:
                pages.append("Train administration")
            page = st.radio("Navigate", pages)
            if st.button("Log out"):
                logout(st.session_state.token, st.session_state.sessions)
                st.session_state.pop("token", None)
                st.session_state.pop("cancel_pending", None)
                st.rerun()
        else:
            st.info("Log in to book and manage tickets.")
            page = st.radio("Navigate", ["Search trains", "Seat availability", "Log in", "Register"])
        st.divider()
        if st.button("Load demo data"):
            try:
                if seed_demo_data(conn):
                    st.success("Demo data loaded.")
                else:
                    st.info("Database already contains trains; demo data was not changed.")
            except ValueError as exc:
                error(exc)
    if page == "Search trains":
        search_screen(conn)
    elif page == "Seat availability":
        availability_screen(conn)
    elif page == "Log in":
        login_screen(conn)
    elif page == "Register":
        register(conn)
    elif user is None:
        st.warning("Please log in to use this feature.")
    elif page == "Book ticket":
        booking_screen(conn, user)
    elif page == "My bookings":
        bookings_screen(conn, user)
    elif page == "Find booking by PNR":
        pnr_screen(conn, user)
    elif page == "Cancel booking":
        cancel_screen(conn, user)
    elif page == "Train administration":
        admin_screen(conn, user)

if __name__ == "__main__":
    main()
