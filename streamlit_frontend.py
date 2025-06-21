import streamlit as st
import pandas as pd
from backend import Participant, generate_unique_name, compute_fair_shares, compute_settlements


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Shared Expense Splitter")
st.title("Shared Expense Splitter")

# ---------- Initialize Session State ----------
if "participants" not in st.session_state:
    st.session_state.participants = []

# ---------- Add Participant Form ----------
with st.form("Add Participant"):
    st.subheader("Add a participant")
    name_input = st.text_input("Name")
    amount_input = st.number_input("Amount spent (may be negative to model borrowing or earnings)", step=2.5, format="%.2f")
    weight_input = st.number_input("Weight (ie 1 for adult, 0.5 for child)", min_value=0.0, value=1.0, step=0.1)
    note_input = st.text_input("Optional note (ie 'paid for fuel')")
    submitted = st.form_submit_button("Add Participant")

    if submitted and name_input:
        recorded_names = [p.name for p in st.session_state.participants]
        unique_name = generate_unique_name(name_input, recorded_names)
        st.session_state.participants.append(Participant(unique_name, amount_input, weight_input, note_input))
        st.success(f"Added: {unique_name}")

# ---------- Display & Edit participants ----------
if st.session_state.participants:
    st.subheader("Participant List")

    # Create DataFrames for display
    df_participants = pd.DataFrame([vars(p) for p in st.session_state.participants])
    total_spent, unit_share, fair_share_data = compute_fair_shares(st.session_state.participants)
    df_fair = pd.DataFrame(fair_share_data)

    # Merge fair share for display
    df_participants_display = df_participants.merge(df_fair[["Name", "Fair Share"]], left_on="name", right_on="Name", how="left")
    df_participants_display.drop(columns=["Name"], inplace=True)

    # Editable table with fair share column disabled
    editable_df = st.data_editor(
        df_participants_display,
        column_config={
            "Fair Share": st.column_config.NumberColumn(disabled=True, help="Calculated from total & weight")
        },
        disabled=["Fair Share"],
        num_rows="fixed",
        use_container_width=True,
        key="participants_editor"
    )

    # Detect and apply edits back to session state only if changes happened
    new_participants = [
        Participant(
            row["name"],
            float(row["amount_spent"]),
            float(row["weight"]),
            row.get("note", "")
        ) for _, row in editable_df.iterrows()
    ]

    # Compare with session state; only update if needed
    if new_participants != st.session_state.participants:
        st.session_state.participants = new_participants
        st.rerun()

    # CSV export
    csv_participants = editable_df.to_csv(index=False).encode("utf-8")

    st.markdown(f"**Total Group Expenses:** {total_spent:.2f}")
    st.markdown(f"**Fair Share for unit Weight:** {unit_share:.2f}")

    # ---------- Settlement Table ----------
    st.markdown("---")
    st.subheader("Settlement Table")

    settlements = compute_settlements(st.session_state.participants)
    if settlements:
        df_settlements = pd.DataFrame(settlements)
        st.dataframe(df_settlements, use_container_width=True)

        # CSV export
        csv_settlements = df_settlements.to_csv(index=False).encode("utf-8")
        
    else:
        st.info("No settlements required — everyone is balanced.")

    # ---------- Delete Participant ----------
    st.markdown("---")
    st.subheader("Remove a Participant")

    participant_names = [p.name for p in st.session_state.participants]
    if "delete_selection" not in st.session_state and participant_names:
        st.session_state.delete_selection = participant_names[0]

    if participant_names:
        selected = st.selectbox("Select participant to remove", options=participant_names, key="delete_dropdown")

        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("Delete Selected"):
                st.session_state.participants = [p for p in st.session_state.participants if p.name != selected]
                st.success(f"Removed: {selected}")
                st.rerun()

    # ---------- Reset App ----------
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1: 
        st.download_button("Export Participants List as CSV", data=csv_participants, file_name="participants.csv", mime="text/csv")
    with col2:
        if st.button("Reset All"):
            st.session_state.participants = []
            st.success("Session cleared.")
            st.rerun()
    with col3:
        if settlements:
            st.download_button("Export Settlements as CSV", data=csv_settlements, file_name="settlements.csv", mime="text/csv")
else:
    st.info("Add at least one participant to execute the programme.")